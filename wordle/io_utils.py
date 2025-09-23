"""Utilities for loading dictionaries and inferring alphabets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Set

DATA_DIR = Path("data")
ANSWERS_PATH = DATA_DIR / "answers.txt"
ALLOWED_PATH = DATA_DIR / "allowed.txt"


@dataclass
class Dictionaries:
    """Container for the words and metadata loaded from disk."""

    answers: List[str]
    allowed: List[str]
    allowed_lookup: Dict[str, str]
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


def _normalise_word(word: str) -> str:
    """Return a canonical representation used for case-insensitive lookups."""

    return word.casefold()


def load_dictionaries() -> Dictionaries:
    """Load dictionary files, creating stubs when missing."""

    missing_files: List[Path] = []
    warnings: List[str] = []

    stub_created = _ensure_stub(ANSWERS_PATH, ["casa", "fiume", "programmazione"])
    stub_created |= _ensure_stub(ALLOWED_PATH, ["casa", "fiume", "programmazione", "gioco"])

    if stub_created:
        warnings.append(
            "Sono stati creati file di esempio in 'data/'. Sostituiscili con i tuoi dizionari."
        )

    if not ANSWERS_PATH.exists():
        missing_files.append(ANSWERS_PATH)
    if not ALLOWED_PATH.exists():
        missing_files.append(ALLOWED_PATH)

    answers: List[str] = []
    allowed: List[str] = []
    allowed_lookup: Dict[str, str] = {}

    def _load(path: Path, target: List[str], *, is_allowed: bool) -> None:
        if not path.exists():
            return
        raw_text = path.read_text(encoding="utf-8")
        for line_number, raw_line in enumerate(raw_text.splitlines(), start=1):
            word = raw_line.strip()
            if not word:
                continue
            if raw_line != word:
                warnings.append(
                    f"Riga {line_number} in {path.name} contiene spazi iniziali/finali ed è stata normalizzata."
                )
            target.append(word)
            normalised = _normalise_word(word)
            if is_allowed and normalised not in allowed_lookup:
                allowed_lookup[normalised] = word

    _load(ANSWERS_PATH, answers, is_allowed=False)
    _load(ALLOWED_PATH, allowed, is_allowed=True)

    # Answers should always be accepted as valid guesses.
    for word in answers:
        normalised = _normalise_word(word)
        allowed_lookup.setdefault(normalised, word)

    if not answers:
        warnings.append(
            "Il file answers.txt è vuoto. Aggiungi almeno una parola per avviare una partita."
        )
    if not allowed:
        warnings.append(
            "Il file allowed.txt è vuoto. Nessun tentativo verrà accettato finché non viene popolato."
        )

    return Dictionaries(
        answers=answers,
        allowed=allowed,
        allowed_lookup=allowed_lookup,
        missing_files=missing_files,
        warnings=warnings,
    )


def infer_alphabet(dictionaries: Dictionaries) -> Set[str]:
    """Infer the alphabet from all available dictionary words."""

    alphabet: Set[str] = set()
    for word in dictionaries.answers + dictionaries.allowed:
        for char in word:
            if char.strip() == "":
                continue
            alphabet.add(char)
    return alphabet

