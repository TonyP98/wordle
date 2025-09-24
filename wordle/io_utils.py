"""Utilities for loading dictionaries and inferring alphabets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Set

DATA_DIR = Path("data")
ANSWERS_PATH = DATA_DIR / "answers.txt"


@dataclass
class Dictionaries:
    """Container for the words and metadata loaded from disk."""

    answers: List[str]
    answers_lookup: Set[str]
    missing_files: List[Path]
    warnings: List[str]


def _ensure_stub(path: Path, sample_words: Iterable[str]) -> bool:
    """Create a minimal stub file if it does not yet exist."""

    if path.exists():
        return False

    path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(sample_words) + "\n"
    path.write_text(content, encoding="utf-8")
    return True


def load_dictionaries() -> Dictionaries:
    """Load dictionary files, creating stubs when missing."""

    missing_files: List[Path] = []
    warnings: List[str] = []

    stub_created = _ensure_stub(ANSWERS_PATH, ["casa", "fiume", "programmazione"])

    if stub_created:
        warnings.append(
            "Sono stati creati file di esempio in 'data/'. Sostituiscili con i tuoi dizionari."
        )

    if not ANSWERS_PATH.exists():
        missing_files.append(ANSWERS_PATH)
    answers: List[str] = []
    if ANSWERS_PATH.exists():
        raw_text = ANSWERS_PATH.read_text(encoding="utf-8")
        for line_number, raw_line in enumerate(raw_text.splitlines(), start=1):
            word = raw_line.strip()
            if not word:
                continue
            if raw_line != word:
                warnings.append(
                    "Riga {} in answers.txt contiene spazi iniziali/finali ed è stata normalizzata.".format(
                        line_number
                    )
                )
            answers.append(word)

    answers_lookup = {word.casefold() for word in answers}

    if not answers:
        warnings.append(
            "Il file answers.txt è vuoto. Aggiungi almeno una parola per avviare una partita."
        )

    return Dictionaries(
        answers=answers,
        answers_lookup=answers_lookup,
        missing_files=missing_files,
        warnings=warnings,
    )


def infer_alphabet(dictionaries: Dictionaries) -> Set[str]:
    """Infer the alphabet from all available dictionary words."""

    alphabet: Set[str] = set()
    for word in dictionaries.answers:
        for char in word:
            if char.strip() == "":
                continue
            alphabet.add(char)
    return alphabet

