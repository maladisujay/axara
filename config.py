import os

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = os.getenv("COMMAND_PREFIX", "a!")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "Asia/Kolkata")

# Embed colours
COLOR_MAIN = 0x7289DA
COLOR_OK = 0x43B581
COLOR_WARN = 0xFAA61A
COLOR_ERROR = 0xF04747

# Levelling
XP_MIN = 15
XP_MAX = 25
XP_COOLDOWN = 60  # seconds between messages that give XP

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
