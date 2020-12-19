import asyncio

import discord
from discord.ext import commands

import config
from utils import chatbot

# Axara also replies to every message in a channel with this name
CHAT_CHANNEL = "chat-with-axara"


class Chat(commands.Cog):
    """Talk to Axara like a (very simple) chatbot."""

    def __init__(self, bot):
        self.bot = bot

    def _should_reply(self, message):
        if message.author.bot:
            return False
        content = message.content.lower()
        if content.startswith(config.PREFIX.lower()):
            return False  # it's a command, let the command handler deal with it
        if isinstance(message.channel, discord.DMChannel):
            return True
        if getattr(message.channel, "name", "") == CHAT_CHANNEL:
            return True
        if self.bot.user in message.mentions:
            return True
        # "hey axara", "axara how are you"
        return content.startswith("axara") or content.startswith("hey axara")

    async def _reply(self, channel, author, text):
        names = ["axara", self.bot.user.name]
        cleaned = chatbot.clean_message(text, names)
        reply = chatbot.get_reply(
            cleaned,
            name=author.display_name,
            bot_name=self.bot.user.name,
            prefix=config.PREFIX,
        )
        async with channel.typing():
            # small delay so it feels like Axara is typing
            await asyncio.sleep(min(0.5 + len(reply) / 80, 2))
            await channel.send(reply)

    @commands.Cog.listener()
    async def on_message(self, message):
        if not self._should_reply(message):
            return
        # a bare mention followed by a command is handled as a command
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return
        await self._reply(message.channel, message.author, message.content)

    @commands.command(name="chat", aliases=["talk"])
    async def chat(self, ctx, *, message: str):
        """Say something to Axara."""
        await self._reply(ctx.channel, ctx.author, message)


def setup(bot):
    bot.add_cog(Chat(bot))
