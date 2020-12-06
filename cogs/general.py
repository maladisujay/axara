import datetime
import platform

import discord
from discord.ext import commands

import config
from utils.timeparse import human_duration

CATEGORIES = {
    "💬 Chat": [
        ("chat <message>", "Talk to Axara (or just mention me / say 'axara ...')"),
    ],
    "🛠️ Utility": [
        ("time [city or timezone]", "Current time somewhere in the world"),
        ("weather <city>", "Current weather for a city"),
        ("convert <value> <from> <to>", "Convert units, e.g. `convert 5 kg g`"),
        ("units", "List units the converter knows"),
    ],
    "🧮 Maths": [
        ("calc <expression>", "Basic calculator, e.g. `calc (5+3)*2`"),
        ("sci <expression>", "Scientific calculator, e.g. `sci sin(30) + log(100)`"),
        ("sci-rad <expression>", "Scientific calculator using radians"),
        ("mathhelp", "Functions the scientific calculator supports"),
    ],
    "📈 Levels": [
        ("rank [member]", "Show your level and XP"),
        ("leaderboard", "Top 10 most active members"),
        ("levelinfo <level>", "XP needed to reach a level"),
        ("setxp <member> <xp>", "Set someone's XP (admin)"),
        ("resetlevels", "Reset all levels in the server (admin)"),
    ],
    "📢 Announcements": [
        ("announce <#channel> <message>", "Post an announcement embed"),
        ("announce-everyone <#channel> <message>", "Announcement that pings @everyone"),
        ("announce-role <#channel> <@role> <message>", "Announcement that pings a role"),
        ("say <#channel> <message>", "Make Axara say something"),
        ("poll <question> | <option 1> | <option 2> ...", "Create a reaction poll"),
    ],
    "🔨 Moderation": [
        ("kick <member> [reason]", "Kick a member"),
        ("ban <member> [reason]", "Ban a member"),
        ("unban <user#1234>", "Unban a user"),
        ("mute <member> [duration] [reason]", "Mute a member, e.g. `mute @user 10m spam`"),
        ("unmute <member>", "Unmute a member"),
        ("warn <member> <reason>", "Warn a member"),
        ("warnings <member>", "See a member's warnings"),
        ("clearwarnings <member>", "Remove a member's warnings (admin)"),
        ("clear <amount>", "Delete recent messages"),
        ("slowmode <seconds>", "Set slowmode for the channel"),
        ("lock / unlock", "Lock or unlock the current channel"),
    ],
    "ℹ️ General": [
        ("help", "This message"),
        ("ping", "Check the bot's latency"),
        ("botinfo", "Info about Axara"),
        ("serverinfo", "Info about this server"),
        ("userinfo [member]", "Info about a member"),
        ("avatar [member]", "Show someone's avatar"),
    ],
}


class General(commands.Cog):
    """Basic commands like help and ping."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help", aliases=["h", "commands"])
    async def help_command(self, ctx, *, command: str = None):
        p = config.PREFIX

        if command:
            cmd = self.bot.get_command(command)
            if cmd is None:
                return await ctx.send(f"There's no command called `{command}`.")
            embed = discord.Embed(
                title=f"{p}{cmd.qualified_name} {cmd.signature}",
                description=cmd.help or "No description.",
                colour=config.COLOR_MAIN,
            )
            if cmd.aliases:
                embed.add_field(name="Aliases", value=", ".join(cmd.aliases))
            return await ctx.send(embed=embed)

        embed = discord.Embed(
            title="Axara — Commands",
            description=f"Prefix: `{p}` • Use `{p}help <command>` for more info.",
            colour=config.COLOR_MAIN,
        )
        for category, cmds in CATEGORIES.items():
            lines = "\n".join(f"`{p}{usage}` — {desc}" for usage, desc in cmds)
            embed.add_field(name=category, value=lines, inline=False)
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command()
    async def ping(self, ctx):
        """Check the bot's latency."""
        await ctx.send(f"🏓 Pong! `{round(self.bot.latency * 1000)}ms`")

    @commands.command(aliases=["about", "info"])
    async def botinfo(self, ctx):
        """Info about Axara."""
        uptime = datetime.datetime.utcnow() - self.bot.launch_time
        embed = discord.Embed(
            title="About Axara",
            description="A friendly multipurpose bot for our server.",
            colour=config.COLOR_MAIN,
        )
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        embed.add_field(name="Servers", value=len(self.bot.guilds))
        embed.add_field(name="Users", value=len(set(self.bot.get_all_members())))
        embed.add_field(name="Uptime", value=human_duration(uptime.total_seconds()), inline=False)
        embed.add_field(name="Python", value=platform.python_version())
        embed.add_field(name="discord.py", value=discord.__version__)
        embed.add_field(name="Prefix", value=f"`{config.PREFIX}`")
        await ctx.send(embed=embed)

    @commands.command(aliases=["server"])
    @commands.guild_only()
    async def serverinfo(self, ctx):
        """Info about this server."""
        g = ctx.guild
        humans = len([m for m in g.members if not m.bot])
        embed = discord.Embed(title=g.name, colour=config.COLOR_MAIN)
        if g.icon:
            embed.set_thumbnail(url=g.icon_url)
        embed.add_field(name="Owner", value=str(g.owner))
        embed.add_field(name="Region", value=str(g.region).title())
        embed.add_field(name="Created", value=g.created_at.strftime("%d %b %Y"))
        embed.add_field(name="Members", value=f"{g.member_count} ({humans} humans)")
        embed.add_field(name="Channels", value=f"{len(g.text_channels)} text / {len(g.voice_channels)} voice")
        embed.add_field(name="Roles", value=len(g.roles))
        embed.set_footer(text=f"ID: {g.id}")
        await ctx.send(embed=embed)

    @commands.command(aliases=["whois", "ui"])
    @commands.guild_only()
    async def userinfo(self, ctx, member: discord.Member = None):
        """Info about a member."""
        member = member or ctx.author
        roles = [r.mention for r in reversed(member.roles) if r != ctx.guild.default_role]
        embed = discord.Embed(title=str(member), colour=member.colour)
        embed.set_thumbnail(url=member.avatar_url)
        embed.add_field(name="Nickname", value=member.nick or "None")
        embed.add_field(name="Bot?", value="Yes" if member.bot else "No")
        embed.add_field(name="Account created", value=member.created_at.strftime("%d %b %Y"))
        embed.add_field(name="Joined server", value=member.joined_at.strftime("%d %b %Y"))
        embed.add_field(
            name=f"Roles ({len(roles)})",
            value=" ".join(roles[:15]) if roles else "None",
            inline=False,
        )
        embed.set_footer(text=f"ID: {member.id}")
        await ctx.send(embed=embed)

    @commands.command(aliases=["av", "pfp"])
    async def avatar(self, ctx, member: discord.Member = None):
        """Show someone's avatar."""
        member = member or ctx.author
        embed = discord.Embed(title=f"{member.display_name}'s avatar", colour=config.COLOR_MAIN)
        embed.set_image(url=member.avatar_url_as(size=512))
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(General(bot))
