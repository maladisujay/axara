<p align="center">
  <img src="assets/axara.png" alt="Axara logo" width="128">
</p>

# Axara

A multipurpose Discord bot for the GITAM community server, written in Python with [discord.py](https://github.com/Rapptz/discord.py).

Axara chats with members using a simple pattern-matching chatbot. It also answers maths questions, converts units, tells the time and weather, helps moderators, posts announcements, and gives members levels based on how much they chat.

## Features

**Chatbot**
- Replies when mentioned, when a message starts with "axara", in DMs, or in any message in a `#chat-with-axara` channel
- Greetings, small talk, jokes, coin flips and dice rolls
- Answers inline maths like "axara what is 12*12"

**Utility**
- `time [city/timezone]`: current time anywhere (defaults to IST)
- `weather <city>`: live weather from OpenWeatherMap
- `convert <value> <from> <to>`: mass, length, volume, time, data, speed and temperature (`convert 5 kg g`, `convert 100 f to c`)

**Calculator**
- `calc`: basic arithmetic with `+ - * / // % ^` and brackets
- `sci`: scientific functions (sin, cos, tan, inverse trig, sqrt, log, ln, factorial, constants pi/e). Uses degrees by default; `sci-rad` uses radians
- Expressions are parsed with Python's `ast` module, not `eval`, so user input is safe to run

**Moderation**
- `kick`, `ban`, `unban`
- `mute [duration]` / `unmute` using a `Muted` role (created automatically), with timed mutes like `10m`, `2h`, `1d`
- `warn`, `warnings`, `clearwarnings` (saved to disk)
- `clear`, `slowmode`, `lock`, `unlock`
- Actions are logged to a `#mod-logs` channel if one exists

**Announcements**
- `announce #channel <message>`: embed announcement (the first line becomes the title, and an attached image is included)
- `announce-everyone` and `announce-role` for pings
- `say` and `poll` (yes/no, or up to 10 options)

**Levels**
- Members earn 15–25 XP per message, at most once per minute
- Level-up messages go to `#level-ups` if that channel exists
- `rank`, `leaderboard`, `levelinfo`, and the admin commands `setxp` / `resetlevels`

Type `a!help` in Discord for the full command list.

## Tech stack

- Python 3.8
- discord.py 1.6.0 (commands extension, cogs, tasks)
- aiohttp (installed with discord.py) for the weather API
- pytz for timezones
- python-dotenv for configuration
- JSON files for storing levels and warnings

## Project structure

```
axara/
├── bot.py              # entry point, loads cogs, global error handler
├── config.py           # settings loaded from .env
├── cogs/
│   ├── general.py      # help, ping, botinfo, serverinfo, userinfo, avatar
│   ├── chat.py         # chatbot listener
│   ├── utility.py      # time, weather, convert
│   ├── calculator.py   # calc, sci
│   ├── moderation.py   # kick, ban, mute, warn, clear ...
│   ├── announcements.py
│   └── levels.py
├── utils/
│   ├── chatbot.py      # reply rules
│   ├── mathparser.py   # safe expression evaluator
│   ├── units.py        # conversion tables
│   ├── leveling.py     # XP formulas
│   ├── timeparse.py    # "10m" / "2h" durations
│   └── storage.py      # JSON load/save
└── data/               # levels.json and warnings.json are created here
```

## Running it

1. Create an application and a bot at the [Discord Developer Portal](https://discord.com/developers/applications).
2. Under **Bot → Privileged Gateway Intents**, turn on **Server Members Intent**.
3. Invite the bot with the `bot` scope and these permissions: Kick Members, Ban Members, Manage Roles, Manage Channels, Manage Messages, Send Messages, Embed Links, Add Reactions, Read Message History, Mention Everyone.
4. Install and configure:

```bash
git clone https://github.com/maladisujay/axara.git
cd axara
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then put your token and weather key in .env
```

5. Start the bot:

```bash
python bot.py
```

Move the bot's role above the roles it needs to moderate, so it can kick, ban and mute those members.

## Configuration

| Variable | Description | Default |
| --- | --- | --- |
| `DISCORD_TOKEN` | Bot token | required |
| `COMMAND_PREFIX` | Command prefix | `a!` |
| `WEATHER_API_KEY` | OpenWeatherMap API key | none (weather disabled) |
| `DEFAULT_TIMEZONE` | Timezone for `time` with no argument | `Asia/Kolkata` |

The bot also responds to its mention as a prefix, e.g. `@Axara help`.
