"""Rendering helpers for the Streamlit interface."""

from __future__ import annotations

import json
from typing import Dict, List, Sequence

import streamlit as st

from .engine import STATUS_EMPTY, STATUS_GRAY, STATUS_GREEN, STATUS_YELLOW, Status

Palette = Dict[str, str]


DEFAULT_PALETTE: Palette = {
    STATUS_GREEN: "#6aaa64",
    STATUS_YELLOW: "#c9b458",
    STATUS_GRAY: "#787c7e",
    STATUS_EMPTY: "#d3d6da",
}

COLOR_BLIND_PALETTE: Palette = {
    STATUS_GREEN: "#f5793a",  # orange
    STATUS_YELLOW: "#85c0f9",  # blue
    STATUS_GRAY: "#5f6a72",
    STATUS_EMPTY: "#c6cbd3",
}

STATUS_EMOJI = {
    STATUS_GREEN: "🟩",
    STATUS_YELLOW: "🟨",
    STATUS_GRAY: "⬜",
    STATUS_EMPTY: "⬜",
}


def get_palette(color_blind: bool) -> Palette:
    """Return the appropriate colour palette."""

    return COLOR_BLIND_PALETTE if color_blind else DEFAULT_PALETTE


def inject_base_styles(answer_length: int, *, color_blind: bool) -> None:
    """Inject CSS required for the board and keyboard."""

    palette = get_palette(color_blind)
    st.markdown(
        f"""
        <style>
        .wordle-board {{
            display: flex;
            flex-direction: column;
            gap: 0.4rem;
            margin-bottom: 1rem;
        }}
        .wordle-row {{
            display: grid;
            grid-template-columns: repeat({answer_length}, minmax(2.4rem, 1fr));
            gap: 0.35rem;
        }}
        .wordle-cell {{
            align-items: center;
            background-color: {palette[STATUS_EMPTY]};
            border-radius: 0.35rem;
            border: 2px solid {palette[STATUS_EMPTY]};
            color: #1f2933;
            display: flex;
            font-size: 1.5rem;
            font-weight: 700;
            justify-content: center;
            min-height: 2.8rem;
            text-transform: uppercase;
        }}
        .wordle-cell.status-green {{
            background-color: {palette[STATUS_GREEN]};
            border-color: {palette[STATUS_GREEN]};
            color: white;
        }}
        .wordle-cell.status-yellow {{
            background-color: {palette[STATUS_YELLOW]};
            border-color: {palette[STATUS_YELLOW]};
            color: #1f1f1f;
        }}
        .wordle-cell.status-gray {{
            background-color: {palette[STATUS_GRAY]};
            border-color: {palette[STATUS_GRAY]};
            color: white;
        }}
        .wordle-keyboard {{
            display: flex;
            flex-direction: column;
            gap: 0.3rem;
            margin-top: 1.2rem;
        }}
        .wordle-keyboard-row {{
            display: flex;
            gap: 0.3rem;
            justify-content: center;
            flex-wrap: wrap;
        }}
        .wordle-key {{
            background-color: {palette[STATUS_EMPTY]};
            border-radius: 0.3rem;
            border: none;
            color: #111827;
            font-weight: 600;
            min-width: 2.2rem;
            padding: 0.55rem 0.4rem;
            text-align: center;
            text-transform: uppercase;
        }}
        .wordle-key.status-green {{
            background-color: {palette[STATUS_GREEN]};
            color: white;
        }}
        .wordle-key.status-yellow {{
            background-color: {palette[STATUS_YELLOW]};
            color: #1f1f1f;
        }}
        .wordle-key.status-gray {{
            background-color: {palette[STATUS_GRAY]};
            color: white;
        }}
        @media (max-width: 600px) {{
            .wordle-row {{
                grid-template-columns: repeat({answer_length}, minmax(1.9rem, 1fr));
            }}
            .wordle-cell {{
                font-size: 1.2rem;
                min-height: 2.2rem;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_board(
    guesses: Sequence[str],
    evaluations: Sequence[Sequence[Status]],
    *,
    answer_length: int,
    max_attempts: int,
    color_blind: bool,
) -> None:
    """Render the main Wordle board."""

    inject_base_styles(answer_length, color_blind=color_blind)

    padded_guesses: List[str] = list(guesses)[:max_attempts]
    padded_evaluations: List[Sequence[Status]] = list(evaluations)[:max_attempts]

    while len(padded_guesses) < max_attempts:
        padded_guesses.append("")
        padded_evaluations.append([STATUS_EMPTY] * answer_length)

    board_html = ["<div class='wordle-board'>"]
    for guess, evaluation in zip(padded_guesses, padded_evaluations):
        row_html = ["<div class='wordle-row'>"]
        letters = list(guess) + [" "] * max(0, answer_length - len(guess))
        for letter, status in zip(letters, evaluation):
            css_class = f"status-{status}"
            content = letter.upper() if letter.strip() else "&nbsp;"
            row_html.append(f"<div class='wordle-cell {css_class}'>{content}</div>")
        row_html.append("</div>")
        board_html.append("".join(row_html))
    board_html.append("</div>")

    st.markdown("".join(board_html), unsafe_allow_html=True)


def render_keyboard(rows: Sequence[Sequence[str]], letter_status: Dict[str, Status], *, color_blind: bool) -> None:
    """Render the optional on-screen keyboard."""

    if not rows:
        return

    mode_class = "color-blind" if color_blind else "default"
    keyboard_html = [f"<div class='wordle-keyboard {mode_class}'>"]
    for row in rows:
        keyboard_html.append("<div class='wordle-keyboard-row'>")
        for key in row:
            normalised_key = key.casefold()
            status = letter_status.get(normalised_key, STATUS_EMPTY)
            keyboard_html.append(
                f"<div class='wordle-key status-{status}'>{key}</div>"
            )
        keyboard_html.append("</div>")
    keyboard_html.append("</div>")
    st.markdown("".join(keyboard_html), unsafe_allow_html=True)


def render_toast(message: str, *, level: str = "info") -> None:
    """Display feedback using the appropriate Streamlit helper."""

    level = level.lower()
    if level == "success":
        st.success(message)
    elif level == "warning":
        st.warning(message)
    elif level == "error":
        st.error(message)
    else:
        st.info(message)


def render_share_button(
    guesses: Sequence[str],
    evaluations: Sequence[Sequence[Status]],
    attempts_used: int,
    max_attempts: int,
) -> None:
    """Render a button that copies the current game result."""

    if not guesses:
        st.button("Condividi risultato", disabled=True)
        return

    emoji_rows = []
    for evaluation in evaluations:
        if not evaluation:
            continue
        emoji_rows.append("".join(STATUS_EMOJI.get(status, "⬜") for status in evaluation))

    if not emoji_rows:
        st.button("Condividi risultato", disabled=True)
        return

    share_text = "Wordle clone — {}/{}".format(attempts_used, max_attempts)
    share_text += "\n" + "\n".join(emoji_rows)

    if st.button("Condividi risultato"):
        payload = json.dumps(share_text)
        st.markdown(
            f"""
            <script>
            const text = {payload};
            navigator.clipboard.writeText(text).then(() => {{
                const toast = window.parent.document.createElement('div');
                toast.innerText = 'Risultato copiato negli appunti!';
                toast.style.position = 'fixed';
                toast.style.bottom = '1.5rem';
                toast.style.left = '50%';
                toast.style.transform = 'translateX(-50%)';
                toast.style.background = 'rgba(17,24,39,0.85)';
                toast.style.color = 'white';
                toast.style.padding = '0.6rem 1rem';
                toast.style.borderRadius = '0.4rem';
                toast.style.zIndex = 9999;
                window.parent.document.body.appendChild(toast);
                setTimeout(() => toast.remove(), 2000);
            }});
            </script>
            """,
            unsafe_allow_html=True,
        )

