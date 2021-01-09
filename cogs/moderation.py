import asyncio
import datetime

import discord
from discord.ext import commands

import config
from utils import storage
from utils.timeparse import human_duration, parse_duration

MUTED_ROLE = "Muted"
LOG_CHANNEL = "mod-logs"


def can_act_on(ctx, member):
    """Moderators can't act on themselves, the owner, or people with a higher role."""
    if member == ctx.author:
        return "You can't do that to yourself."
    if member == ctx.guild.owner:
        return "You can't do that to the server owner."
    if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
        return "That member's role is higher than or equal to yours."
    if member.top_role >= ctx.guild.me.top_role:
        return "That member's role is higher than mine, so I can't touch them."
    return None


class Moderation(commands.Cog):
    """Commands for moderators."""

    def __init__(self, bot):
        self.bot = bot
        self.warnings = storage.load("warnings")
        self.mute_tasks = {}

    def cog_check(self, ctx):
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        return True

    async def log(self, guild, title, member, moderator, reason, colour=config.COLOR_WARN):
        channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL)
        if channel is None:
            return
        embed = discord.Embed(title=title, colour=colour, timestamp=datetime.datetime.utcnow())
        embed.add_field(name="Member", value=f"{member} ({member.id})")
        embed.add_field(name="Moderator", value=str(moderator))
        embed.add_field(name="Reason", value=reason or "No reason given", inline=False)
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            pass

    async def get_muted_role(self, guild):
        role = discord.utils.get(guild.roles, name=MUTED_ROLE)
        if role:
            return role

        role = await guild.create_role(name=MUTED_ROLE, reason="Mute role for Axara")
        # stop the role from talking anywhere
        for channel in guild.channels:
            try:
                await channel.set_permissions(
                    role, send_messages=False, add_reactions=False, speak=False
                )
            except discord.Forbidden:
                continue
        return role

    async def _dm(self, member, text):
        try:
            await member.send(text)
        except (discord.Forbidden, discord.HTTPException):
            pass  # DMs closed

    @commands.command()
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = None):
        """Kick a member from the server."""
        problem = can_act_on(ctx, member)
        if problem:
            return await ctx.send(problem)

        await self._dm(member, f"You were kicked from **{ctx.guild.name}**. Reason: {reason or 'none'}")
        await member.kick(reason=f"{ctx.author}: {reason}")
        await ctx.send(f"👢 **{member}** was kicked. Reason: {reason or 'none'}")
        await self.log(ctx.guild, "Member kicked", member, ctx.author, reason)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = None):
        """Ban a member from the server."""
        problem = can_act_on(ctx, member)
        if problem:
            return await ctx.send(problem)

        await self._dm(member, f"You were banned from **{ctx.guild.name}**. Reason: {reason or 'none'}")
        await member.ban(reason=f"{ctx.author}: {reason}", delete_message_days=0)
        await ctx.send(f"🔨 **{member}** was banned. Reason: {reason or 'none'}")
        await self.log(ctx.guild, "Member banned", member, ctx.author, reason, config.COLOR_ERROR)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx, *, user: str):
        """Unban a user by name#discriminator or ID."""
        bans = await ctx.guild.bans()
        for entry in bans:
            u = entry.user
            if str(u) == user or str(u.id) == user:
                await ctx.guild.unban(u, reason=f"Unbanned by {ctx.author}")
                await ctx.send(f"✅ Unbanned **{u}**")
                return await self.log(ctx.guild, "Member unbanned", u, ctx.author, None, config.COLOR_OK)
        await ctx.send(f"I couldn't find a banned user called `{user}`.")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, duration: str = None, *, reason: str = None):
        """Mute a member. Duration is optional, e.g. 10m, 2h, 1d."""
        problem = can_act_on(ctx, member)
        if problem:
            return await ctx.send(problem)

        seconds = parse_duration(duration)
        if duration and seconds is None:
            # the "duration" was actually the start of the reason
            reason = f"{duration} {reason}" if reason else duration

        role = await self.get_muted_role(ctx.guild)
        if role in member.roles:
            return await ctx.send(f"**{member}** is already muted.")

        await member.add_roles(role, reason=f"{ctx.author}: {reason}")
        length = human_duration(seconds) if seconds else "until unmuted"
        await ctx.send(f"🔇 **{member}** was muted ({length}). Reason: {reason or 'none'}")
        await self.log(ctx.guild, f"Member muted ({length})", member, ctx.author, reason)

        if seconds:
            task = self.bot.loop.create_task(self._unmute_later(member, role, seconds))
            self.mute_tasks[(ctx.guild.id, member.id)] = task

    async def _unmute_later(self, member, role, seconds):
        await asyncio.sleep(seconds)
        try:
            # fetch again in case the member's roles changed
            member = member.guild.get_member(member.id) or member
            if role in member.roles:
                await member.remove_roles(role, reason="Mute expired")
        except discord.HTTPException:
            pass
        self.mute_tasks.pop((member.guild.id, member.id), None)

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member):
        """Unmute a member."""
        role = discord.utils.get(ctx.guild.roles, name=MUTED_ROLE)
        if role is None or role not in member.roles:
            return await ctx.send(f"**{member}** isn't muted.")

        await member.remove_roles(role, reason=f"Unmuted by {ctx.author}")
        task = self.mute_tasks.pop((ctx.guild.id, member.id), None)
        if task:
            task.cancel()
        await ctx.send(f"🔊 **{member}** was unmuted.")
        await self.log(ctx.guild, "Member unmuted", member, ctx.author, None, config.COLOR_OK)

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str):
        """Warn a member. Warnings are saved."""
        if member.bot:
            return await ctx.send("You can't warn a bot.")

        guild_warns = self.warnings.setdefault(str(ctx.guild.id), {})
        user_warns = guild_warns.setdefault(str(member.id), [])
        user_warns.append({
            "reason": reason,
            "moderator": str(ctx.author),
            "date": datetime.datetime.utcnow().strftime("%d %b %Y"),
        })
        storage.save("warnings", self.warnings)

        await self._dm(member, f"⚠️ You were warned in **{ctx.guild.name}**: {reason}")
        await ctx.send(f"⚠️ **{member}** has been warned. They now have {len(user_warns)} warning(s).")
        await self.log(ctx.guild, "Member warned", member, ctx.author, reason)

    @commands.command(aliases=["warns"])
    @commands.has_permissions(kick_members=True)
    async def warnings(self, ctx, member: discord.Member):
        """See a member's warnings."""
        user_warns = self.warnings.get(str(ctx.guild.id), {}).get(str(member.id), [])
        if not user_warns:
            return await ctx.send(f"**{member}** has no warnings. 😇")

        embed = discord.Embed(title=f"Warnings for {member}", colour=config.COLOR_WARN)
        for i, w in enumerate(user_warns[-10:], start=1):
            embed.add_field(
                name=f"#{i} — {w['date']}",
                value=f"{w['reason']}\n*by {w['moderator']}*",
                inline=False,
            )
        await ctx.send(embed=embed)

    @commands.command(aliases=["clearwarns"])
    @commands.has_permissions(administrator=True)
    async def clearwarnings(self, ctx, member: discord.Member):
        """Remove all warnings for a member."""
        self.warnings.get(str(ctx.guild.id), {}).pop(str(member.id), None)
        storage.save("warnings", self.warnings)
        await ctx.send(f"Cleared all warnings for **{member}**.")

    @commands.command(aliases=["purge"])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int = 10):
        """Delete recent messages (max 100)."""
        if amount < 1 or amount > 100:
            return await ctx.send("Pick a number between 1 and 100.")
        deleted = await ctx.channel.purge(limit=amount + 1)  # +1 for the command itself
        msg = await ctx.send(f"🧹 Deleted {len(deleted) - 1} messages.")
        await msg.delete(delay=3)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int = 0):
        """Set slowmode for this channel (0 to turn off)."""
        if seconds < 0 or seconds > 21600:
            return await ctx.send("Slowmode has to be between 0 and 21600 seconds.")
        await ctx.channel.edit(slowmode_delay=seconds)
        if seconds == 0:
            await ctx.send("Slowmode is now off.")
        else:
            await ctx.send(f"🐢 Slowmode set to {seconds} seconds.")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def lock(self, ctx):
        """Stop @everyone from talking in this channel."""
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send("🔒 Channel locked.")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def unlock(self, ctx):
        """Let @everyone talk in this channel again."""
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=None)
        await ctx.send("🔓 Channel unlocked.")


def setup(bot):
    bot.add_cog(Moderation(bot))
