"""
Level maths.

XP needed to go from level n to n+1 is 5n² + 50n + 100, so each level
takes a bit longer than the last one.
"""


def xp_for_next(level):
    return 5 * level ** 2 + 50 * level + 100


def total_xp_for_level(level):
    """Total XP needed to reach a level starting from 0."""
    return sum(xp_for_next(l) for l in range(level))


def level_from_xp(xp):
    """Returns (level, xp into the current level, xp needed for the next level)."""
    level = 0
    while xp >= xp_for_next(level):
        xp -= xp_for_next(level)
        level += 1
    return level, xp, xp_for_next(level)


def progress_bar(current, total, length=12):
    filled = int(length * current / total) if total else 0
    return "▰" * filled + "▱" * (length - filled)
