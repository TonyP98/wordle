from datetime import datetime, timedelta

from zoneinfo import ZoneInfo

from wordle.daily import get_daily_index, select_daily_word


ROME = ZoneInfo("Europe/Rome")


def test_daily_index_same_day():
    answers = ["casa", "fiume", "albero"]
    reference = datetime(2021, 6, 19, 10, tzinfo=ROME)
    assert get_daily_index(answers, reference) == 0
    assert select_daily_word(answers, reference) == "casa"


def test_daily_index_next_day():
    answers = ["casa", "fiume", "albero"]
    reference = datetime(2021, 6, 20, 1, tzinfo=ROME)
    assert get_daily_index(answers, reference) == 1


def test_daily_index_wraps():
    answers = ["casa", "fiume", "albero"]
    start = datetime(2021, 6, 19, 8, tzinfo=ROME)
    future = start + timedelta(days=5)
    assert get_daily_index(answers, future) == (5 % len(answers))

