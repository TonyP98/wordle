from wordle.engine import STATUS_GREEN, STATUS_YELLOW, score_guess


def test_duplicates_with_accents():
    guess = "APPÀ"
    answer = "PAPÀ"
    assert score_guess(guess, answer) == [
        STATUS_YELLOW,
        STATUS_YELLOW,
        STATUS_GREEN,
        STATUS_GREEN,
    ]


def test_duplicates_with_repeated_letters():
    guess = "LLANOBO"
    answer = "BALLOON"
    assert score_guess(guess, answer) == [
        STATUS_YELLOW,
        STATUS_YELLOW,
        STATUS_YELLOW,
        STATUS_YELLOW,
        STATUS_GREEN,
        STATUS_YELLOW,
        STATUS_YELLOW,
    ]

