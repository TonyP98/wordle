from __future__ import annotations

import random
from typing import Dict, List, Sequence

import streamlit as st

from wordle.daily import get_daily_index, select_daily_word
from wordle.engine import (
    MAX_ATTEMPTS,
    STATUS_GRAY,
    STATUS_GREEN,
    STATUS_YELLOW,
    ValidationError,
    build_hard_mode_constraints,
    score_guess,
    validate_guess,
)
from wordle.io_utils import Dictionaries, infer_alphabet, load_dictionaries
from wordle.keyboard import build_keyboard_rows, should_show_keyboard
from wordle.render import render_board, render_keyboard, render_share_button, render_toast

st.set_page_config(page_title="Wordle senza limiti", page_icon="🔤", layout="centered")

SYSTEM_RANDOM = random.SystemRandom()


def _init_session_state() -> None:
    st.session_state.setdefault("mode", "daily")
    st.session_state.setdefault("max_attempts", MAX_ATTEMPTS)
    st.session_state.setdefault("color_blind", False)
    st.session_state.setdefault("hard_mode", False)
    st.session_state.setdefault("stats", {
        "played": 0,
        "wins": 0,
        "current_streak": 0,
        "max_streak": 0,
        "distribution": {},
    })
    st.session_state.setdefault("guess_input", "")
    st.session_state.setdefault("clear_guess_input", False)
    st.session_state.setdefault("game_over", False)
    st.session_state.setdefault("answer", "")
    st.session_state.setdefault("answer_signature", "")
    st.session_state.setdefault("guesses", [])
    st.session_state.setdefault("evaluations", [])
    st.session_state.setdefault("result_recorded", False)


def _start_new_round(answer: str, *, signature: str) -> None:
    st.session_state["answer"] = answer
    st.session_state["answer_signature"] = signature
    st.session_state["guesses"] = []
    st.session_state["evaluations"] = []
    st.session_state["game_over"] = False
    st.session_state["result_recorded"] = False
    st.session_state["clear_guess_input"] = True


def _choose_free_word(answers: Sequence[str]) -> str:
    return SYSTEM_RANDOM.choice(list(answers))


def _update_stats(win: bool, attempts_used: int) -> None:
    stats = st.session_state.get("stats", {})
    stats.setdefault("distribution", {})
    stats.setdefault("played", 0)
    stats.setdefault("wins", 0)
    stats.setdefault("current_streak", 0)
    stats.setdefault("max_streak", 0)

    stats["played"] += 1
    if win:
        stats["wins"] += 1
        stats["current_streak"] += 1
        stats["max_streak"] = max(stats["max_streak"], stats["current_streak"])
        dist = stats["distribution"]
        dist[attempts_used] = dist.get(attempts_used, 0) + 1
    else:
        stats["current_streak"] = 0

    st.session_state["stats"] = stats
    st.session_state["result_recorded"] = True


def _rerun() -> None:
    rerun = getattr(st, "experimental_rerun", None)
    if rerun is not None:
        rerun()
    else:
        st.rerun()


def _ensure_answer(dictionaries: Dictionaries, mode: str) -> None:
    answers = dictionaries.answers
    if not answers:
        return

    max_attempts = st.session_state.get("max_attempts", MAX_ATTEMPTS)
    current_signature = st.session_state.get("answer_signature", "")

    if mode == "daily":
        index = get_daily_index(answers)
        signature = f"daily-{index}"
        if current_signature != signature:
            answer = select_daily_word(answers)
            _start_new_round(answer, signature=signature)
    else:
        if not current_signature.startswith("free-"):
            answer = _choose_free_word(answers)
            signature = f"free-{SYSTEM_RANDOM.randrange(1_000_000_000)}"
            _start_new_round(answer, signature=signature)
        elif not st.session_state.get("answer"):
            answer = _choose_free_word(answers)
            signature = f"free-{SYSTEM_RANDOM.randrange(1_000_000_000)}"
            _start_new_round(answer, signature=signature)

    # Adjust board if max attempts decreased below current guesses.
    guesses = st.session_state.get("guesses", [])
    evaluations = st.session_state.get("evaluations", [])
    if len(guesses) > max_attempts:
        st.session_state["guesses"] = guesses[:max_attempts]
        st.session_state["evaluations"] = evaluations[:max_attempts]


def _build_letter_status(guesses: Sequence[str], evaluations: Sequence[Sequence[str]]) -> Dict[str, str]:
    priority = {STATUS_GRAY: 0, STATUS_YELLOW: 1, STATUS_GREEN: 2}
    letter_status: Dict[str, str] = {}
    for guess, evaluation in zip(guesses, evaluations):
        for letter, status in zip(guess, evaluation):
            if not letter.strip():
                continue
            normalised = letter.casefold()
            if normalised not in letter_status or priority[status] > priority[letter_status[normalised]]:
                letter_status[normalised] = status
    return letter_status


def _show_stats() -> None:
    stats = st.session_state.get("stats", {})
    played = stats.get("played", 0)
    wins = stats.get("wins", 0)
    win_rate = (wins / played * 100) if played else 0
    st.sidebar.markdown("### Statistiche")
    st.sidebar.metric("Partite", played)
    st.sidebar.metric("Vittorie", wins)
    st.sidebar.metric("Win rate", f"{win_rate:.0f}%")
    st.sidebar.metric("Streak", f"{stats.get('current_streak', 0)} / {stats.get('max_streak', 0)}")

    distribution = stats.get("distribution", {})
    if distribution:
        st.sidebar.markdown("#### Distribuzione tentativi")
        for attempt in sorted(distribution):
            st.sidebar.write(f"{attempt}: {distribution[attempt]}")


def main() -> None:
    _init_session_state()

    dictionaries = load_dictionaries()
    alphabet = infer_alphabet(dictionaries)

    with st.sidebar:
        st.markdown("### Impostazioni")
        max_attempts = st.slider(
            "Tentativi massimi",
            min_value=4,
            max_value=10,
            value=st.session_state.get("max_attempts", MAX_ATTEMPTS),
        )
        st.session_state["max_attempts"] = max_attempts
        st.session_state["color_blind"] = st.checkbox(
            "Palette accessibile",
            value=st.session_state.get("color_blind", False),
        )
        st.session_state["hard_mode"] = st.checkbox(
            "Modalità difficile",
            value=st.session_state.get("hard_mode", False),
        )
        _show_stats()

    st.title("Wordle senza limiti")

    mode_radio = st.radio(
        "Modalità di gioco",
        options=("Daily", "Free play"),
        index=0 if st.session_state.get("mode") == "daily" else 1,
        horizontal=True,
    )
    mode = "daily" if mode_radio == "Daily" else "free"
    if mode != st.session_state.get("mode"):
        st.session_state["mode"] = mode
        st.session_state["answer_signature"] = ""
        st.session_state["answer"] = ""
        st.session_state["guesses"] = []
        st.session_state["evaluations"] = []
        st.session_state["game_over"] = False
        st.session_state["result_recorded"] = False

    st.selectbox("Dizionario", options=["Predefinito"], index=0, help="Altri dizionari arriveranno in futuro.")

    if dictionaries.warnings:
        for warning in dictionaries.warnings:
            render_toast(warning, level="warning")

    if dictionaries.missing_files:
        render_toast(
            "Carica i file in 'data/answers.txt' e 'data/allowed.txt' per iniziare a giocare.",
            level="error",
        )
        return

    if not dictionaries.answers or not dictionaries.allowed:
        render_toast(
            "I dizionari devono contenere almeno una parola per poter giocare.",
            level="error",
        )
        return

    _ensure_answer(dictionaries, mode)

    answer = st.session_state.get("answer", "")
    if not answer:
        render_toast("Impossibile selezionare una parola. Controlla i dizionari.", level="error")
        return

    answer_length = len(answer)
    max_attempts = st.session_state.get("max_attempts", MAX_ATTEMPTS)
    color_blind = st.session_state.get("color_blind", False)
    hard_mode = st.session_state.get("hard_mode", False)

    st.caption(f"Parola di {answer_length} lettere")
    st.caption("Modalità: {}".format("Daily" if mode == "daily" else "Free play"))

    guesses: List[str] = st.session_state.get("guesses", [])
    evaluations: List[List[str]] = st.session_state.get("evaluations", [])

    render_board(guesses, evaluations, answer_length=answer_length, max_attempts=max_attempts, color_blind=color_blind)

    show_keyboard = should_show_keyboard(alphabet)
    if show_keyboard:
        keyboard_rows = build_keyboard_rows(alphabet)
        letter_status = _build_letter_status(guesses, evaluations)
        render_keyboard(keyboard_rows, letter_status, color_blind=color_blind)

    if st.session_state.get("game_over") and not st.session_state.get("result_recorded"):
        win = any(all(status == STATUS_GREEN for status in eval_row) for eval_row in evaluations)
        _update_stats(win, len(guesses))

    game_over = st.session_state.get("game_over", False)

    with st.form("guess_form", clear_on_submit=False):
        if st.session_state.get("clear_guess_input"):
            st.session_state["guess_input"] = ""
            st.session_state["clear_guess_input"] = False
        guess_value = st.text_input(
            "Inserisci un tentativo",
            value=st.session_state.get("guess_input", ""),
            key="guess_input",
            help="Premi Invio oppure usa i pulsanti sottostanti.",
            disabled=game_over,
        )
        col_submit, col_clear, col_new = st.columns(3)
        submit = col_submit.form_submit_button("Invia", disabled=game_over)
        clear = col_clear.form_submit_button("Cancella")
        new_game = col_new.form_submit_button("Nuova partita")

    if clear:
        st.session_state["clear_guess_input"] = True
        _rerun()
        return

    if new_game:
        if mode == "daily":
            signature = st.session_state.get("answer_signature", "")
            _start_new_round(answer, signature=signature or "daily-reset")
        else:
            fresh_answer = _choose_free_word(dictionaries.answers)
            signature = f"free-{SYSTEM_RANDOM.randrange(1_000_000_000)}"
            _start_new_round(fresh_answer, signature=signature)
        _rerun()
        return

    if submit and not game_over:
        guess = guess_value
        try:
            history = list(zip(guesses, evaluations))
            hard_constraints = None
            if hard_mode and history:
                hard_constraints = build_hard_mode_constraints(history)
            validate_guess(
                guess,
                answer,
                dictionaries.allowed_lookup,
                hard_constraints=hard_constraints,
            )
        except ValidationError as exc:
            render_toast(str(exc), level="warning")
        else:
            normalised = "".join(ch.casefold() for ch in guess)
            canonical = dictionaries.allowed_lookup.get(normalised, guess)
            evaluation = score_guess(canonical, answer)
            guesses.append(canonical)
            evaluations.append(evaluation)
            st.session_state["guesses"] = guesses
            st.session_state["evaluations"] = evaluations
            st.session_state["clear_guess_input"] = True

            if all(status == STATUS_GREEN for status in evaluation):
                st.session_state["game_over"] = True
                render_toast("Complimenti! Hai indovinato la parola.", level="success")
            elif len(guesses) >= max_attempts:
                st.session_state["game_over"] = True
                render_toast(f"Tentativi esauriti. La parola era '{answer}'.", level="error")

            _rerun()
            return

    attempts_used = len(guesses)
    render_share_button(guesses, evaluations, attempts_used, max_attempts)


if __name__ == "__main__":
    main()
