import discord
from discord.ext import commands

import config
from utils import mathparser


class Calculator(commands.Cog):
    """Basic and scientific calculator."""

    def __init__(self, bot):
        self.bot = bot

    async def _calculate(self, ctx, expression, degrees=True, title="Calculator"):
        try:
            result = mathparser.evaluate(expression, degrees=degrees)
        except mathparser.CalcError as e:
            return await ctx.send(f"❌ {e}")

        embed = discord.Embed(title=f"🧮 {title}", colour=config.COLOR_MAIN)
        embed.add_field(name="Input", value=f"```{expression}```", inline=False)
        embed.add_field(name="Result", value=f"```{mathparser.format_number(result)}```", inline=False)
        await ctx.send(embed=embed)

    @commands.command(aliases=["calculate", "math", "c"])
    async def calc(self, ctx, *, expression: str):
        """Basic calculator. Supports + - * / ^ % and brackets."""
        await self._calculate(ctx, expression)

    @commands.command(aliases=["scientific", "scical"])
    async def sci(self, ctx, *, expression: str):
        """Scientific calculator (angles in degrees)."""
        await self._calculate(ctx, expression, degrees=True, title="Scientific (degrees)")

    @commands.command(name="sci-rad", aliases=["scirad"])
    async def sci_rad(self, ctx, *, expression: str):
        """Scientific calculator (angles in radians)."""
        await self._calculate(ctx, expression, degrees=False, title="Scientific (radians)")

    @commands.command()
    async def mathhelp(self, ctx):
        """Functions the scientific calculator understands."""
        embed = discord.Embed(title="Scientific calculator", colour=config.COLOR_MAIN)
        embed.add_field(name="Operators", value="`+ - * / // % ^` and `( )`", inline=False)
        embed.add_field(
            name="Trigonometry",
            value="`sin cos tan asin acos atan sinh cosh tanh`",
            inline=False,
        )
        embed.add_field(
            name="Other functions",
            value="`sqrt cbrt log ln log2 exp abs round floor ceil fact rad deg`",
            inline=False,
        )
        embed.add_field(name="Constants", value="`pi e tau`", inline=False)
        embed.add_field(
            name="Examples",
            value=(
                f"`{config.PREFIX}sci sin(30)` → 0.5\n"
                f"`{config.PREFIX}sci log(1000)` → 3\n"
                f"`{config.PREFIX}sci sqrt(144) + 2^3` → 20\n"
                f"`{config.PREFIX}sci fact(5)` → 120\n"
                f"`{config.PREFIX}sci log(8, 2)` → 3"
            ),
            inline=False,
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Calculator(bot))
