import datetime

import aiohttp
import discord
import pytz
from discord.ext import commands

import config
from utils import units as unit_tables
from utils.mathparser import format_number

WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

# so people can type a city instead of a full timezone name
CITY_TIMEZONES = {
    "vizag": "Asia/Kolkata",
    "visakhapatnam": "Asia/Kolkata",
    "hyderabad": "Asia/Kolkata",
    "bangalore": "Asia/Kolkata",
    "bengaluru": "Asia/Kolkata",
    "delhi": "Asia/Kolkata",
    "mumbai": "Asia/Kolkata",
    "chennai": "Asia/Kolkata",
    "india": "Asia/Kolkata",
    "ist": "Asia/Kolkata",
    "london": "Europe/London",
    "uk": "Europe/London",
    "paris": "Europe/Paris",
    "berlin": "Europe/Berlin",
    "dubai": "Asia/Dubai",
    "singapore": "Asia/Singapore",
    "tokyo": "Asia/Tokyo",
    "sydney": "Australia/Sydney",
    "new york": "America/New_York",
    "nyc": "America/New_York",
    "est": "America/New_York",
    "chicago": "America/Chicago",
    "los angeles": "America/Los_Angeles",
    "la": "America/Los_Angeles",
    "pst": "America/Los_Angeles",
    "california": "America/Los_Angeles",
    "toronto": "America/Toronto",
    "utc": "UTC",
    "gmt": "UTC",
}

WEATHER_EMOJI = {
    "Clear": "☀️",
    "Clouds": "☁️",
    "Rain": "🌧️",
    "Drizzle": "🌦️",
    "Thunderstorm": "⛈️",
    "Snow": "❄️",
    "Mist": "🌫️",
    "Haze": "🌫️",
    "Fog": "🌫️",
    "Smoke": "🌫️",
}


def _find_timezone(place):
    place = place.strip().lower()
    if place in CITY_TIMEZONES:
        return pytz.timezone(CITY_TIMEZONES[place])
    # try a direct match like "Asia/Tokyo"
    for tz in pytz.all_timezones:
        if tz.lower() == place:
            return pytz.timezone(tz)
    # try matching just the city part, e.g. "tokyo" -> "Asia/Tokyo"
    for tz in pytz.all_timezones:
        if tz.lower().split("/")[-1].replace("_", " ") == place:
            return pytz.timezone(tz)
    return None


class Utility(commands.Cog):
    """Time, weather and unit conversions."""

    def __init__(self, bot):
        self.bot = bot
        self.session = None

    async def get_session(self):
        # the session has to be created inside a coroutine
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    def cog_unload(self):
        if self.session:
            self.bot.loop.create_task(self.session.close())

    @commands.command(aliases=["clock", "date"])
    async def time(self, ctx, *, place: str = None):
        """Show the current time. Defaults to India time."""
        if place:
            tz = _find_timezone(place)
            if tz is None:
                return await ctx.send(
                    f"I don't know the timezone for `{place}`. "
                    "Try a city like `tokyo` or a zone like `Europe/London`."
                )
        else:
            tz = pytz.timezone(config.DEFAULT_TIMEZONE)

        now = datetime.datetime.now(tz)
        embed = discord.Embed(
            title=f"🕒 {now.strftime('%I:%M %p')}",
            description=now.strftime("%A, %d %B %Y"),
            colour=config.COLOR_MAIN,
        )
        embed.set_footer(text=f"{tz.zone} (UTC{now.strftime('%z')[:3]}:{now.strftime('%z')[3:]})")
        await ctx.send(embed=embed)

    @commands.command(aliases=["w"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def weather(self, ctx, *, city: str):
        """Current weather for a city."""
        if not config.WEATHER_API_KEY:
            return await ctx.send("Weather isn't set up yet (missing API key).")

        params = {"q": city, "appid": config.WEATHER_API_KEY, "units": "metric"}
        async with ctx.typing():
            try:
                session = await self.get_session()
                async with session.get(WEATHER_URL, params=params) as resp:
                    data = await resp.json()
            except aiohttp.ClientError:
                return await ctx.send("I couldn't reach the weather service, try again later.")

        if str(data.get("cod")) != "200":
            return await ctx.send(f"I couldn't find weather for `{city}`.")

        main = data["main"]
        condition = data["weather"][0]
        emoji = WEATHER_EMOJI.get(condition["main"], "🌡️")
        country = data.get("sys", {}).get("country", "")

        embed = discord.Embed(
            title=f"{emoji} Weather in {data['name']}, {country}",
            description=condition["description"].capitalize(),
            colour=config.COLOR_MAIN,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.add_field(name="Temperature", value=f"{main['temp']:.1f}°C")
        embed.add_field(name="Feels like", value=f"{main['feels_like']:.1f}°C")
        embed.add_field(name="Min / Max", value=f"{main['temp_min']:.0f}° / {main['temp_max']:.0f}°")
        embed.add_field(name="Humidity", value=f"{main['humidity']}%")
        embed.add_field(name="Wind", value=f"{data['wind']['speed'] * 3.6:.1f} km/h")
        embed.add_field(name="Pressure", value=f"{main['pressure']} hPa")
        embed.set_thumbnail(url=f"https://openweathermap.org/img/wn/{condition['icon']}@2x.png")
        embed.set_footer(text="Data from OpenWeatherMap")
        await ctx.send(embed=embed)

    @commands.command(aliases=["conv", "cv"])
    async def convert(self, ctx, value: float, from_unit: str, *args):
        """Convert units, e.g. `convert 5 kg g` or `convert 100 f to c`."""
        args = [a for a in args if a.lower() != "to"]
        if not args:
            return await ctx.send(f"Usage: `{config.PREFIX}convert 5 kg g`")
        to_unit = args[0]

        try:
            result = unit_tables.convert(value, from_unit, to_unit)
        except unit_tables.ConversionError as e:
            return await ctx.send(f"{e} Use `{config.PREFIX}units` to see what I know.")

        await ctx.send(
            f"🔁 **{format_number(value)} {from_unit}** = **{format_number(round(result, 6))} {to_unit}**"
        )

    @commands.command()
    async def units(self, ctx):
        """List the units the converter supports."""
        embed = discord.Embed(
            title="Supported units",
            description=unit_tables.supported_units(),
            colour=config.COLOR_MAIN,
        )
        embed.set_footer(text=f"Example: {config.PREFIX}convert 2.5 kg g")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Utility(bot))
