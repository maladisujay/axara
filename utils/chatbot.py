"""
Axara's little chatbot brain.

It's a simple pattern matcher: each rule is a list of regex patterns and
a list of possible replies. The first rule that matches wins and a random
reply is picked. Replies can use {name} for the person's display name and
{bot} for the bot's name.
"""
import random
import re

from utils import mathparser

RULES = [
    # greetings
    (
        [r"\b(hi|hello|hey|hii+|heyy+|yo|hola|namaste|sup)\b"],
        [
            "Hey {name}! 👋",
            "Hello {name}! How's it going?",
            "Hi there {name}! What's up?",
            "Heyy {name} 😄",
        ],
    ),
    (
        [r"good morning", r"\bgm\b"],
        ["Good morning {name}! ☀️ Have a great day.", "Morning {name}! Got classes today?"],
    ),
    (
        [r"good night", r"\bgn\b"],
        ["Good night {name} 🌙 Sleep well!", "Night {name}! See you tomorrow."],
    ),
    (
        [r"good (afternoon|evening)"],
        ["Good {match} to you too, {name}!"],
    ),
    # how are you
    (
        [r"how (are|r) (you|u)", r"how('?s| is) it going", r"wh?at'?s up", r"\bwassup\b"],
        [
            "I'm doing great, thanks for asking! How about you?",
            "All systems running smoothly 🤖 How are you?",
            "Just hanging out in the server. You?",
        ],
    ),
    (
        [r"\bi('?m| am) (good|fine|great|ok|okay|doing well)\b"],
        ["Glad to hear that {name}! 😊", "Nice! Keep it up."],
    ),
    (
        [r"\bi('?m| am) (sad|bored|tired|stressed|not ok)\b"],
        [
            "Aw, sorry to hear that {name}. Take a break, you deserve it 💙",
            "Hang in there {name}! Maybe chat with your friends here for a bit?",
        ],
    ),
    # about the bot
    (
        [r"who are you", r"what are you", r"your name", r"introduce yourself"],
        [
            "I'm {bot}, the bot for this server! I can chat, do maths, convert units, "
            "tell the time and weather, and keep track of levels. Type `{prefix}help` to see everything.",
        ],
    ),
    (
        [r"who (made|created|built) you", r"your (creator|owner|developer)"],
        ["I was made by the admin of this server using Python and discord.py 🐍"],
    ),
    (
        [r"how old are you", r"your age"],
        ["I was born in 2020, so I'm pretty young for a bot!"],
    ),
    (
        [r"are you (a )?(bot|robot|human|real)"],
        ["Yep, I'm a bot 🤖 But a friendly one!", "100% bot, 0% human. Beep boop."],
    ),
    (
        [r"what can you do", r"\bhelp me\b", r"your (commands|features)"],
        [
            "I can do quite a few things! Try `{prefix}help` for the full list. "
            "Some favourites: `{prefix}calc`, `{prefix}weather`, `{prefix}convert`, `{prefix}rank`.",
        ],
    ),
    # feelings towards the bot
    (
        [r"\b(i love you|love you|ily)\b"],
        ["Aww, I love you too {name} ❤️", "You're making my circuits blush 😳"],
    ),
    (
        [r"\b(thanks|thank you|thx|ty)\b"],
        ["You're welcome {name}!", "Anytime! 😄", "No problem!"],
    ),
    (
        [r"\b(stupid|dumb|useless|idiot)\b"],
        ["Hey, I'm still learning! 😅", "That's not very nice... I'm trying my best."],
    ),
    (
        [r"\b(lol|lmao|haha+|xd)\b"],
        ["😂", "Haha glad you're having fun!", "lol"],
    ),
    # fun stuff
    (
        [r"tell (me )?a joke", r"\bjoke\b"],
        [
            "Why do programmers prefer dark mode? Because light attracts bugs. 🐛",
            "Why did the student eat his homework? Because the teacher said it was a piece of cake.",
            "I told my computer I needed a break, and it said 'No problem, I'll go to sleep.'",
            "Why was the maths book sad? It had too many problems.",
            "What do you call a fake noodle? An impasta. 🍝",
            "How many programmers does it take to change a light bulb? None, that's a hardware problem.",
        ],
    ),
    (
        [r"flip a coin", r"coin ?flip", r"heads or tails"],
        ["🪙 It's **Heads**!", "🪙 It's **Tails**!"],
    ),
    (
        [r"roll a dice", r"roll a die", r"\broll\b"],
        ["🎲 You rolled a **{dice}**!"],
    ),
    (
        [r"favou?rite (colou?r)"],
        ["Blurple, obviously 💜"],
    ),
    (
        [r"favou?rite (food)"],
        ["I run on electricity, but biryani sounds amazing."],
    ),
    (
        [r"favou?rite (movie|song|game)"],
        ["Hard to choose! What's yours?"],
    ),
    (
        [r"(do you|u) (sleep|eat)"],
        ["Nope, I'm online 24/7 (unless my host goes down 😬)."],
    ),
    (
        [r"(exam|exams|test|assignment|semester)"],
        [
            "Good luck with your studies {name}! 📚 You've got this.",
            "Study hard but don't forget to take breaks!",
        ],
    ),
    (
        [r"\b(bye|goodbye|see ya|cya|ttyl)\b"],
        ["Bye {name}! 👋", "See you later {name}!", "Take care!"],
    ),
]

FALLBACKS = [
    "Hmm, I'm not sure what you mean 🤔",
    "I didn't quite get that. Try asking something else!",
    "Interesting... tell me more?",
    "I'm just a simple bot, I don't understand everything yet 😅",
    "Sorry {name}, I don't know how to answer that. Try `{prefix}help`.",
]

# "what is 5 + 5", "calculate 12*3", "solve 2^10"
MATH_PATTERN = re.compile(
    r"(?:what(?:'s| is)|calculate|calc|solve|compute)\s+([0-9\.\s\+\-\*/\^\(\)%!]+)\??$",
    re.IGNORECASE,
)

COMPILED = [([re.compile(p, re.IGNORECASE) for p in patterns], replies) for patterns, replies in RULES]


def clean_message(text, bot_names):
    text = text.lower()
    for name in bot_names:
        text = text.replace(name.lower(), " ")
    text = re.sub(r"<@!?\d+>", " ", text)  # strip mentions
    return " ".join(text.split())


def get_reply(text, name, bot_name="Axara", prefix="a!"):
    """Return a reply string for a message, or a fallback if nothing matches."""
    fmt = {
        "name": name,
        "bot": bot_name,
        "prefix": prefix,
        "dice": random.randint(1, 6),
    }

    math_match = MATH_PATTERN.search(text)
    if math_match:
        try:
            result = mathparser.evaluate(math_match.group(1))
            return f"That's **{mathparser.format_number(result)}** 🧮"
        except mathparser.CalcError as e:
            return str(e)

    for patterns, replies in COMPILED:
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                fmt["match"] = match.group(1) if match.groups() else match.group(0)
                return random.choice(replies).format(**fmt)

    return random.choice(FALLBACKS).format(**fmt)
