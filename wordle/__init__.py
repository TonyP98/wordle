"""Core package for the unlimited-length Wordle clone."""

from .engine import MAX_ATTEMPTS, score_guess, validate_guess
from .daily import get_daily_index, select_daily_word
from .io_utils import load_dictionaries, infer_alphabet

__all__ = [
    "MAX_ATTEMPTS",
    "score_guess",
    "validate_guess",
    "get_daily_index",
    "select_daily_word",
    "load_dictionaries",
    "infer_alphabet",
]
