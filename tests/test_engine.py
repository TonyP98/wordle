import pytest

from wordle.engine import (
    STATUS_GREEN,
    STATUS_GRAY,
    STATUS_YELLOW,
    ValidationError,
    build_hard_mode_constraints,
    score_guess,
    validate_guess,
)


def test_score_guess_all_green():
    assert score_guess("casa", "casa") == [STATUS_GREEN] * 4


def test_score_guess_mixed_lengths():
    guess = "gessato"
    answer = "gestire"
    assert score_guess(guess, answer) == [
        STATUS_GREEN,
        STATUS_GREEN,
        STATUS_GREEN,
        STATUS_GRAY,
        STATUS_GRAY,
        STATUS_YELLOW,
        STATUS_GRAY,
    ]


def test_validate_guess_length_mismatch():
    with pytest.raises(ValidationError):
        validate_guess("casa", "casale")


def test_validate_guess_unknown_word_is_allowed():
    # Any word is accepted provided it satisfies length requirements.
    validate_guess("laghi", "fiume")


def test_validate_guess_hard_mode_constraints():
    answer = "cane"
    first_guess = "casa"
    evaluation = score_guess(first_guess, answer)
    history = [(first_guess, evaluation)]
    constraints = build_hard_mode_constraints(history)

    with pytest.raises(ValidationError):
        validate_guess("coro", answer, hard_constraints=constraints)

    # Correctly reusing greens succeeds.
    validate_guess("cane", answer, hard_constraints=constraints)

