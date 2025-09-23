"""Game engine utilities for the unlimited-length Wordle clone."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import List, Sequence, Tuple

MAX_ATTEMPTS = 6

STATUS_GREEN = "green"
STATUS_YELLOW = "yellow"
STATUS_GRAY = "gray"
STATUS_EMPTY = "empty"

Status = str


def _normalise_letter(letter: str) -> str:
    """Return a normalised representation of a single character."""

    return letter.casefold()


@dataclass
class HardModeConstraints:
    """Container for the constraints enforced in hard mode.

    Attributes
    ----------
    fixed_positions:
        Mapping position -> normalised letter that must appear in that slot.
    min_letter_counts:
        Minimum occurrences required for each normalised letter.
    disallowed_positions:
        Mapping position -> set of normalised letters that cannot appear there.
    letter_display:
        Mapping normalised letter -> representative character to use in messages.
    """

    fixed_positions: dict[int, str]
    min_letter_counts: dict[str, int]
    disallowed_positions: dict[int, set[str]]
    letter_display: dict[str, str]

    def display_letter(self, normalised: str) -> str:
        """Return a user-friendly letter for feedback messages."""

        return self.letter_display.get(normalised, normalised.upper())


class ValidationError(ValueError):
    """Raised when a guess cannot be accepted."""


def score_guess(guess: str, answer: str) -> List[Status]:
    """Score a guess against the answer using Wordle's two-pass algorithm.

    This implementation works with words of arbitrary length and supports any
    Unicode characters without normalising accents or diacritics.
    """

    if len(guess) != len(answer):
        raise ValueError("Guess and answer must have the same length for scoring.")

    answer_letters = list(answer)
    guess_letters = list(guess)

    answer_norm = [_normalise_letter(ch) for ch in answer_letters]
    guess_norm = [_normalise_letter(ch) for ch in guess_letters]

    statuses: List[Status] = [STATUS_GRAY] * len(answer_letters)
    residual_counts: Counter[str] = Counter()

    # First pass: mark greens and gather residual counts from the answer.
    for idx, (g_norm, a_norm) in enumerate(zip(guess_norm, answer_norm)):
        if g_norm == a_norm:
            statuses[idx] = STATUS_GREEN
        else:
            residual_counts[a_norm] += 1

    # Second pass: assign yellow where applicable and grey otherwise.
    for idx, g_norm in enumerate(guess_norm):
        if statuses[idx] == STATUS_GREEN:
            continue
        if residual_counts[g_norm] > 0:
            statuses[idx] = STATUS_YELLOW
            residual_counts[g_norm] -= 1
        else:
            statuses[idx] = STATUS_GRAY

    return statuses


def build_hard_mode_constraints(history: Sequence[Tuple[str, Sequence[Status]]]) -> HardModeConstraints:
    """Compute hard mode constraints based on the full guess history."""

    fixed_positions: dict[int, str] = {}
    min_letter_counts: dict[str, int] = {}
    disallowed_positions: dict[int, set[str]] = defaultdict(set)
    letter_display: dict[str, str] = {}

    for guess, statuses in history:
        guess_norm = [_normalise_letter(ch) for ch in guess]
        per_guess_counts: Counter[str] = Counter()
        for idx, (letter, norm, status) in enumerate(zip(guess, guess_norm, statuses)):
            letter_display.setdefault(norm, letter)
            if status == STATUS_GREEN:
                fixed_positions[idx] = norm
                per_guess_counts[norm] += 1
            elif status == STATUS_YELLOW:
                disallowed_positions[idx].add(norm)
                per_guess_counts[norm] += 1
        for norm, count in per_guess_counts.items():
            if count > min_letter_counts.get(norm, 0):
                min_letter_counts[norm] = count

    # Ensure the disallowed sets are plain sets (not defaultdicts) for clarity.
    disallowed_positions = {idx: set(letters) for idx, letters in disallowed_positions.items()}

    return HardModeConstraints(
        fixed_positions=fixed_positions,
        min_letter_counts=min_letter_counts,
        disallowed_positions=disallowed_positions,
        letter_display=letter_display,
    )


def validate_guess(
    guess: str,
    answer: str,
    allowed_lookup: dict[str, str],
    *,
    hard_constraints: HardModeConstraints | None = None,
) -> None:
    """Validate a guess against the active rules.

    Parameters
    ----------
    guess:
        The raw string entered by the user.
    answer:
        The current secret word.
    allowed_lookup:
        Mapping of normalised words to their canonical representation.
    hard_constraints:
        Optional hard mode requirements that must be satisfied.

    Raises
    ------
    ValidationError
        If the guess violates any rule.
    """

    if not guess:
        raise ValidationError("Inserisci una parola prima di inviare il tentativo.")

    if guess.strip() != guess:
        raise ValidationError("Rimuovi spazi iniziali o finali dalla parola inserita.")

    guess_letters = list(guess)
    guess_norm = [_normalise_letter(ch) for ch in guess_letters]

    if len(guess_norm) != len(answer):
        raise ValidationError(
            f"La parola deve contenere esattamente {len(answer)} caratteri."
        )

    normalised_word = "".join(guess_norm)
    if normalised_word not in allowed_lookup:
        raise ValidationError("La parola non è presente nel dizionario consentito.")

    if hard_constraints is None:
        return

    # Enforce fixed positions (greens).
    for idx, required_letter in hard_constraints.fixed_positions.items():
        if guess_norm[idx] != required_letter:
            display = hard_constraints.display_letter(required_letter)
            raise ValidationError(
                f"La modalità difficile richiede la lettera '{display}' nella posizione {idx + 1}."
            )

    # Enforce minimum counts for discovered letters.
    guess_counter = Counter(guess_norm)
    for letter, minimum in hard_constraints.min_letter_counts.items():
        if guess_counter.get(letter, 0) < minimum:
            display = hard_constraints.display_letter(letter)
            raise ValidationError(
                f"La modalità difficile richiede almeno {minimum} occorrenze della lettera '{display}'."
            )

    # Enforce that yellow letters are not placed in previously invalid positions.
    for idx, letters in hard_constraints.disallowed_positions.items():
        if idx in hard_constraints.fixed_positions:
            continue
        if guess_norm[idx] in letters:
            display = hard_constraints.display_letter(guess_norm[idx])
            raise ValidationError(
                "La modalità difficile vieta di ripetere una lettera nota nella stessa posizione."
            )


