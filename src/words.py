"""Load English and Kinyarwanda interface copy from locale JSON files."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALE = ROOT / "locale"


def _months(block: dict) -> dict:
    names = block.get("month_names")
    if isinstance(names, dict):
        block["month_names"] = {int(key): value for key, value in names.items()}
    return block


def load_text() -> dict:
    english = json.loads((LOCALE / "en.json").read_text(encoding="utf-8"))
    kinyarwanda = json.loads((LOCALE / "rw.json").read_text(encoding="utf-8"))
    return {"en": _months(english), "rw": _months(kinyarwanda)}


TEXT = load_text()
