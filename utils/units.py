"""
Unit conversion tables.

Every unit in a category is stored as how many of the "base" unit it is
(grams for mass, metres for length, etc.). Converting is then just
value * from_factor / to_factor. Temperature is special and handled
separately.
"""

UNITS = {
    "mass": {
        "mg": 0.001, "milligram": 0.001, "milligrams": 0.001,
        "g": 1, "gram": 1, "grams": 1,
        "kg": 1000, "kgs": 1000, "kilogram": 1000, "kilograms": 1000,
        "t": 1_000_000, "tonne": 1_000_000, "tonnes": 1_000_000, "ton": 1_000_000,
        "lb": 453.59237, "lbs": 453.59237, "pound": 453.59237, "pounds": 453.59237,
        "oz": 28.349523125, "ounce": 28.349523125, "ounces": 28.349523125,
    },
    "length": {
        "mm": 0.001, "millimeter": 0.001, "millimeters": 0.001,
        "cm": 0.01, "centimeter": 0.01, "centimeters": 0.01,
        "m": 1, "meter": 1, "meters": 1, "metre": 1, "metres": 1,
        "km": 1000, "kilometer": 1000, "kilometers": 1000, "kms": 1000,
        "in": 0.0254, "inch": 0.0254, "inches": 0.0254,
        "ft": 0.3048, "foot": 0.3048, "feet": 0.3048,
        "yd": 0.9144, "yard": 0.9144, "yards": 0.9144,
        "mi": 1609.344, "mile": 1609.344, "miles": 1609.344,
    },
    "volume": {
        "ml": 0.001, "milliliter": 0.001, "milliliters": 0.001,
        "l": 1, "liter": 1, "liters": 1, "litre": 1, "litres": 1,
        "gal": 3.785411784, "gallon": 3.785411784, "gallons": 3.785411784,
        "cup": 0.24, "cups": 0.24,
    },
    "time": {
        "ms": 0.001, "millisecond": 0.001, "milliseconds": 0.001,
        "s": 1, "sec": 1, "second": 1, "seconds": 1,
        "min": 60, "mins": 60, "minute": 60, "minutes": 60,
        "h": 3600, "hr": 3600, "hrs": 3600, "hour": 3600, "hours": 3600,
        "day": 86400, "days": 86400,
        "week": 604800, "weeks": 604800,
        "year": 31536000, "years": 31536000,
    },
    "data": {
        "b": 1, "byte": 1, "bytes": 1,
        "kb": 1024, "kilobyte": 1024, "kilobytes": 1024,
        "mb": 1024 ** 2, "megabyte": 1024 ** 2, "megabytes": 1024 ** 2,
        "gb": 1024 ** 3, "gigabyte": 1024 ** 3, "gigabytes": 1024 ** 3,
        "tb": 1024 ** 4, "terabyte": 1024 ** 4, "terabytes": 1024 ** 4,
    },
    "speed": {
        "m/s": 1, "mps": 1,
        "km/h": 1 / 3.6, "kmh": 1 / 3.6, "kph": 1 / 3.6, "kmph": 1 / 3.6,
        "mph": 0.44704,
    },
}

TEMPERATURE = {
    "c": "c", "celsius": "c", "°c": "c",
    "f": "f", "fahrenheit": "f", "°f": "f",
    "k": "k", "kelvin": "k",
}


class ConversionError(Exception):
    pass


def _find_category(unit):
    for category, table in UNITS.items():
        if unit in table:
            return category
    return None


def _convert_temperature(value, src, dst):
    # convert to celsius first, then to the target
    if src == "f":
        c = (value - 32) * 5 / 9
    elif src == "k":
        c = value - 273.15
    else:
        c = value

    if dst == "f":
        return c * 9 / 5 + 32
    if dst == "k":
        return c + 273.15
    return c


def convert(value, src, dst):
    src = src.lower().strip()
    dst = dst.lower().strip()

    if src in TEMPERATURE and dst in TEMPERATURE:
        return _convert_temperature(value, TEMPERATURE[src], TEMPERATURE[dst])

    src_cat = _find_category(src)
    dst_cat = _find_category(dst)

    if src_cat is None:
        raise ConversionError(f"I don't know the unit `{src}`.")
    if dst_cat is None:
        raise ConversionError(f"I don't know the unit `{dst}`.")
    if src_cat != dst_cat:
        raise ConversionError(f"You can't convert {src_cat} into {dst_cat}!")

    table = UNITS[src_cat]
    return value * table[src] / table[dst]


def supported_units():
    lines = []
    for category, table in UNITS.items():
        # only show the short names so the list isn't huge
        short = sorted({u for u in table if len(u) <= 4}, key=lambda u: table[u])
        lines.append(f"**{category.title()}**: {', '.join(short)}")
    lines.append("**Temperature**: c, f, k")
    return "\n".join(lines)
