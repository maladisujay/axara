import random
import time

import discord
from discord.ext import commands, tasks

import config
from utils import leveling, storage

# optional: if a channel with this name exists, level-up messages go there
LEVEL_CHANNEL = "level-ups"


class Levels(commands.Cog):
    """XP and levels based on how much people chat."""

    def __init__(self, bot):
        self.bot = bot
        # {guild_id: {user_id: {"xp": int, "messages": int}}}
        self.data = storage.load("levels")
        self.cooldowns = {}
        self.dirty = False
        self.autosave.start()

    def cog_unload(self):
        self.autosave.cancel()
        self.save()

    def save(self):
        if self.dirty:
            storage.save("levels", self.data)
            self.dirty = False

    @tasks.loop(seconds=60)
    async def autosave(self):
        self.save()

    def get_user(self, guild_id, user_id):
        guild = self.data.setdefault(str(guild_id), {})
        return guild.setdefault(str(user_id), {"xp": 0, "messages": 0})

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.guild is None:
            return
        if message.content.startswith(config.PREFIX):
            return  # commands don't count

        user = self.get_user(message.guild.id, message.author.id)
        user["messages"] += 1
        self.dirty = True

        # only give XP once per minute so spamming doesn't help
        key = (message.guild.id, message.author.id)
        now = time.time()
        if now - self.cooldowns.get(key, 0) < config.XP_COOLDOWN:
            return
        self.cooldowns[key] = now

        old_level = leveling.level_from_xp(user["xp"])[0]
        user["xp"] += random.randint(config.XP_MIN, config.XP_MAX)
        new_level = leveling.level_from_xp(user["xp"])[0]

        if new_level > old_level:
            channel = discord.utils.get(message.guild.text_channels, name=LEVEL_CHANNEL) or message.channel
            try:
                await channel.send(
                    f"🎉 GG {message.author.mention}, you just reached **level {new_level}**!"
                )
            except discord.Forbidden:
                pass

    def _rank_position(self, guild_id, user_id):
        users = self.data.get(str(guild_id), {})
        ordered = sorted(users.items(), key=lambda kv: kv[1]["xp"], reverse=True)
        for pos, (uid, _) in enumerate(ordered, start=1):
            if uid == str(user_id):
                return pos, len(ordered)
        return None, len(ordered)

    @commands.command(aliases=["level", "lvl", "xp"])
    @commands.guild_only()
    async def rank(self, ctx, member: discord.Member = None):
        """Show your (or someone else's) level."""
        member = member or ctx.author
        if member.bot:
            return await ctx.send("Bots don't get levels 🤖")

        user = self.get_user(ctx.guild.id, member.id)
        level, current, needed = leveling.level_from_xp(user["xp"])
        pos, total = self._rank_position(ctx.guild.id, member.id)

        embed = discord.Embed(colour=member.colour if member.colour.value else config.COLOR_MAIN)
        embed.set_author(name=str(member), icon_url=member.avatar_url)
        embed.add_field(name="Rank", value=f"#{pos} of {total}" if pos else "Unranked")
        embed.add_field(name="Level", value=str(level))
        embed.add_field(name="Total XP", value=str(user["xp"]))
        embed.add_field(
            name=f"Progress to level {level + 1}",
            value=f"{leveling.progress_bar(current, needed)} {current}/{needed} XP",
            inline=False,
        )
        embed.set_footer(text=f"{user['messages']} messages sent")
        await ctx.send(embed=embed)

    @commands.command(aliases=["lb", "top"])
    @commands.guild_only()
    async def leaderboard(self, ctx):
        """Top 10 most active members."""
        users = self.data.get(str(ctx.guild.id), {})
        ordered = sorted(users.items(), key=lambda kv: kv[1]["xp"], reverse=True)

        lines = []
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        for uid, info in ordered:
            member = ctx.guild.get_member(int(uid))
            if member is None:
                continue  # left the server
            pos = len(lines) + 1
            level = leveling.level_from_xp(info["xp"])[0]
            badge = medals.get(pos, f"`#{pos}`")
            lines.append(f"{badge} **{member.display_name}** — Level {level} ({info['xp']} XP)")
            if len(lines) == 10:
                break

        if not lines:
            return await ctx.send("Nobody has any XP yet. Start chatting! 💬")

        embed = discord.Embed(
            title=f"🏆 {ctx.guild.name} Leaderboard",
            description="\n".join(lines),
            colour=config.COLOR_MAIN,
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def levelinfo(self, ctx, level: int):
        """How much XP you need to reach a level."""
        if level < 1 or level > 200:
            return await ctx.send("Pick a level between 1 and 200.")
        total = leveling.total_xp_for_level(level)
        avg = (config.XP_MIN + config.XP_MAX) / 2
        msgs = int(total / avg) + 1
        await ctx.send(
            f"📈 Level **{level}** needs **{total:,} XP** in total "
            f"(about {msgs:,} messages, one per minute)."
        )

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def setxp(self, ctx, member: discord.Member, xp: int):
        """Set a member's XP (admin only)."""
        user = self.get_user(ctx.guild.id, member.id)
        user["xp"] = max(0, xp)
        self.dirty = True
        level = leveling.level_from_xp(user["xp"])[0]
        await ctx.send(f"Set **{member}** to {user['xp']} XP (level {level}).")

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def resetlevels(self, ctx):
        """Reset everyone's levels in this server (admin only)."""
        await ctx.send("Are you sure? This resets **all** levels. Type `yes` to confirm.")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            reply = await self.bot.wait_for("message", check=check, timeout=20)
        except Exception:
            return await ctx.send("Cancelled.")
        if reply.content.lower() != "yes":
            return await ctx.send("Cancelled.")

        self.data[str(ctx.guild.id)] = {}
        self.dirty = True
        self.save()
        await ctx.send("All levels have been reset.")


def setup(bot):
    bot.add_cog(Levels(bot))
