import json
from pathlib import Path


def load_shortcuts(path):
    path = Path(path)
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig") as file:
        data = json.load(file)
    return data if isinstance(data, list) else []
