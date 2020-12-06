import re

UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400}
PATTERN = re.compile(r"(\d+)\s*([smhd])", re.IGNORECASE)


def parse_duration(text):
    """Turn strings like '10m', '1h30m' or '2d' into seconds. Returns None if invalid."""
    if not text:
        return None
    text = text.strip().lower()
    matches = PATTERN.findall(text)
    if not matches or PATTERN.sub("", text).strip():
        return None
    return sum(int(num) * UNITS[unit] for num, unit in matches)


def human_duration(seconds):
    seconds = int(seconds)
    parts = []
    for name, size in (("day", 86400), ("hour", 3600), ("minute", 60), ("second", 1)):
        if seconds >= size:
            amount, seconds = divmod(seconds, size)
            parts.append(f"{amount} {name}{'s' if amount != 1 else ''}")
    return ", ".join(parts) if parts else "0 seconds"
