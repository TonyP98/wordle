"""Helpers to build an optional virtual keyboard."""

from __future__ import annotations

from typing import List, Set

BASIC_QWERTY_ROWS = [
    "QWERTYUIOP",
    "ASDFGHJKL",
    "ZXCVBNM",
]


def should_show_keyboard(alphabet: Set[str]) -> bool:
    """Return True if the inferred alphabet is small enough for a keyboard."""

    if not alphabet:
        return False
    if len(alphabet) > 40:
        return False
    return all(len(char) == 1 and char.isprintable() and not char.isspace() for char in alphabet)


def build_keyboard_rows(alphabet: Set[str]) -> List[List[str]]:
    """Organise the alphabet into keyboard rows."""

    if not alphabet:
        return []

    uppercase_letters = {char.upper() for char in alphabet}
    english_letters = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    rows: List[List[str]] = []

    if uppercase_letters <= english_letters:
        used: Set[str] = set()
        for pattern in BASIC_QWERTY_ROWS:
            row = [char for char in pattern if char in uppercase_letters]
            if row:
                rows.append(row)
                used.update(row)
        remaining = sorted(uppercase_letters - used)
        if remaining:
            rows.append(remaining)
        return rows

    # Generic fallback: sort and chunk into rows of max 10 symbols.
    sorted_chars = sorted(alphabet, key=lambda c: c.upper())
    current_row: List[str] = []
    for char in sorted_chars:
        display_char = char.upper() if len(char) == 1 else char
        current_row.append(display_char)
        if len(current_row) >= 10:
            rows.append(current_row)
            current_row = []
    if current_row:
        rows.append(current_row)

    return rows

