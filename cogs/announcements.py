import datetime

import discord
from discord.ext import commands

import config

NUMBER_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]


class Announcements(commands.Cog):
    """Announcements, polls and messages from Axara."""

    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx):
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        return True

    def _announcement_embed(self, ctx, message):
        # first line becomes the title if there's more than one line
        lines = message.split("\n", 1)
        if len(lines) == 2 and len(lines[0]) <= 256:
            title, body = lines
        else:
            title, body = "📢 Announcement", message

        embed = discord.Embed(
            title=title,
            description=body,
            colour=config.COLOR_MAIN,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        embed.set_footer(text=f"Posted by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)

        # attach the first image the moderator uploaded, if any
        for attachment in ctx.message.attachments:
            if attachment.filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                embed.set_image(url=attachment.url)
                break
        return embed

    async def _post(self, ctx, channel, message, ping=None):
        perms = channel.permissions_for(ctx.guild.me)
        if not (perms.send_messages and perms.embed_links):
            return await ctx.send(f"I can't post embeds in {channel.mention}.")

        embed = self._announcement_embed(ctx, message)
        allowed = discord.AllowedMentions(everyone=ping is not None, roles=True, users=True)
        await channel.send(content=ping, embed=embed, allowed_mentions=allowed)
        if channel != ctx.channel:
            await ctx.send(f"✅ Announcement posted in {channel.mention}")

    @commands.command(aliases=["ann"])
    @commands.has_permissions(manage_messages=True)
    async def announce(self, ctx, channel: discord.TextChannel, *, message: str):
        """Post an announcement embed. Put the title on the first line."""
        await self._post(ctx, channel, message)

    @commands.command(name="announce-everyone", aliases=["annall"])
    @commands.has_permissions(mention_everyone=True)
    async def announce_everyone(self, ctx, channel: discord.TextChannel, *, message: str):
        """Post an announcement and ping @everyone."""
        await self._post(ctx, channel, message, ping="@everyone")

    @commands.command(name="announce-role", aliases=["annrole"])
    @commands.has_permissions(manage_messages=True)
    async def announce_role(self, ctx, channel: discord.TextChannel, role: discord.Role, *, message: str):
        """Post an announcement and ping a role."""
        await self._post(ctx, channel, message, ping=role.mention)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def say(self, ctx, channel: discord.TextChannel, *, message: str):
        """Make Axara say something in a channel."""
        await channel.send(message, allowed_mentions=discord.AllowedMentions.none())
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def poll(self, ctx, *, text: str):
        """Make a poll. Use `poll Question | option 1 | option 2`, or just a question for yes/no."""
        parts = [p.strip() for p in text.split("|") if p.strip()]
        question, options = parts[0], parts[1:]

        if len(options) > len(NUMBER_EMOJIS):
            return await ctx.send("A poll can have at most 10 options.")
        if len(options) == 1:
            return await ctx.send("A poll needs at least 2 options (or none for yes/no).")

        embed = discord.Embed(title=f"📊 {question}", colour=config.COLOR_MAIN)
        embed.set_footer(text=f"Poll by {ctx.author.display_name}")

        if options:
            embed.description = "\n".join(
                f"{NUMBER_EMOJIS[i]} {opt}" for i, opt in enumerate(options)
            )
            reactions = NUMBER_EMOJIS[: len(options)]
        else:
            reactions = ["👍", "👎", "🤷"]

        msg = await ctx.send(embed=embed)
        for emoji in reactions:
            await msg.add_reaction(emoji)
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass


def setup(bot):
    bot.add_cog(Announcements(bot))
