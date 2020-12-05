import json
import os

import config


def _path(name):
    return os.path.join(config.DATA_DIR, f"{name}.json")


def load(name, default=None):
    """Load a JSON file from the data folder, returning default if missing."""
    path = _path(name)
    if not os.path.exists(path):
        return {} if default is None else default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        print(f"Could not read {path}, starting fresh")
        return {} if default is None else default


def save(name, data):
    os.makedirs(config.DATA_DIR, exist_ok=True)
    path = _path(name)
    tmp = path + ".tmp"
    # write to a temp file first so a crash mid-write doesn't wipe the data
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)
