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
        validate_guess("casa", "casale", {"casa": "casa"})


def test_validate_guess_unknown_word():
    allowed_lookup = {"casa": "casa", "fiume": "fiume"}
    with pytest.raises(ValidationError):
        validate_guess("lago", "fiume", allowed_lookup)


def test_validate_guess_hard_mode_constraints():
    answer = "cane"
    first_guess = "casa"
    evaluation = score_guess(first_guess, answer)
    history = [(first_guess, evaluation)]
    constraints = build_hard_mode_constraints(history)
    allowed_lookup = {
        "casa": "casa",
        "cane": "cane",
        "coro": "coro",
    }

    with pytest.raises(ValidationError):
        validate_guess("coro", answer, allowed_lookup, hard_constraints=constraints)

    # Correctly reusing greens succeeds.
    validate_guess("cane", answer, allowed_lookup, hard_constraints=constraints)

