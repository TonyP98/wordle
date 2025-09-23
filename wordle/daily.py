"""Daily word selection logic based on the Europe/Rome timezone."""

from __future__ import annotations

from datetime import date, datetime
from typing import Sequence

from zoneinfo import ZoneInfo

EUROPE_ROME = ZoneInfo("Europe/Rome")
BASE_DATE = date(2021, 6, 19)


def get_daily_index(answers: Sequence[str], reference: datetime | None = None) -> int:
    """Return the deterministic index for the daily word.

    The index is derived from the number of days elapsed since BASE_DATE in the
    Europe/Rome timezone and wraps around when exceeding the answers list.
    """

    if not answers:
        raise ValueError("La lista delle risposte è vuota; impossibile selezionare una parola.")

    if reference is None:
        reference = datetime.now(tz=EUROPE_ROME)
    else:
        reference = reference.astimezone(EUROPE_ROME)

    current_date = reference.date()
    delta_days = (current_date - BASE_DATE).days
    index = delta_days % len(answers)
    return index


def select_daily_word(answers: Sequence[str], reference: datetime | None = None) -> str:
    """Return today's word from the provided answers list."""

    index = get_daily_index(answers, reference=reference)
    return answers[index]

