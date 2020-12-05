import datetime
import os

import discord
from discord.ext import commands

import config

intents = discord.Intents.default()
intents.members = True  # needed for moderation, ranks and the leaderboard

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(config.PREFIX),
    intents=intents,
    case_insensitive=True,
    help_command=None,
)
bot.launch_time = datetime.datetime.utcnow()

EXTENSIONS = [
    "cogs.general",
    "cogs.chat",
    "cogs.utility",
    "cogs.calculator",
    "cogs.moderation",
    "cogs.announcements",
    "cogs.levels",
]


@bot.event
async def on_ready():
    print("------")
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"Connected to {len(bot.guilds)} server(s)")
    print("------")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening, name=f"{config.PREFIX}help"
        )
    )


@bot.event
async def on_command_error(ctx, error):
    # let commands with their own error handler deal with it
    if hasattr(ctx.command, "on_error"):
        return

    error = getattr(error, "original", error)

    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            f"You missed the `{error.param.name}` argument. "
            f"Try `{config.PREFIX}help {ctx.command.name}`."
        )
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use that command.")
    elif isinstance(error, commands.BotMissingPermissions):
        perms = ", ".join(p.replace("_", " ") for p in error.missing_perms)
        await ctx.send(f"I need these permissions to do that: **{perms}**")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("I couldn't find that member.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"Bad argument: {error}")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"Slow down! Try again in {error.retry_after:.1f}s.")
    elif isinstance(error, commands.NoPrivateMessage):
        await ctx.send("That command only works inside a server.")
    elif isinstance(error, discord.Forbidden):
        await ctx.send("I'm not allowed to do that (check my role position).")
    else:
        await ctx.send("Something went wrong while running that command.")
        print(f"Error in command {ctx.command}: {error!r}")


if __name__ == "__main__":
    if not config.TOKEN:
        raise SystemExit("DISCORD_TOKEN is missing. Copy .env.example to .env first.")

    os.makedirs(config.DATA_DIR, exist_ok=True)

    for ext in EXTENSIONS:
        try:
            bot.load_extension(ext)
            print(f"Loaded {ext}")
        except Exception as e:
            print(f"Failed to load {ext}: {e}")

    bot.run(config.TOKEN)
