from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from verify.sbsolver import (
    InputIssue,
    analyze_letter_sets,
    parse_letter_sets,
)


st.set_page_config(page_title="SB Solver Center Matrix", page_icon="🐝", layout="wide")

st.title("🐝 SB Solver Center Matrix")
st.caption(
    "Compare SB Solver word counts for every possible center letter using Chrome."
)

with st.sidebar:
    st.header("Display settings")
    bold_min = st.number_input("Bold range minimum", min_value=0, value=35, step=1)
    bold_max = st.number_input("Bold range maximum", min_value=0, value=90, step=1)
    if bold_min > bold_max:
        st.warning("The minimum must be no greater than the maximum.")
    st.caption("Both endpoints are included.")

raw_input = st.text_area(
    "Seven-letter sets",
    height=220,
    placeholder="PLANETS\nORCHIDS\n...",
    help="Use one set per line, or separate sets with commas or spaces. Each set must contain exactly seven different A–Z letters.",
)


def make_display_frame(results: list[dict]) -> pd.DataFrame:
    rows = []
    for result in results:
        row = {"Letter set": result["letter_set"]}
        for position, item in enumerate(result["centers"], start=1):
            row[f"Center {position}"] = f'{item["letter"]}: {item["count"]}'
        rows.append(row)
    return pd.DataFrame(rows)


def emphasize_target_range(value: object) -> str:
    if not isinstance(value, str) or ":" not in value:
        return ""
    try:
        count = int(value.rsplit(":", 1)[1].strip())
    except ValueError:
        return ""
    return "color: green" if bold_min <= count <= bold_max else ""


def render_results(results: list[dict]) -> None:
    display_frame = make_display_frame(results)
    center_columns = [
        column for column in display_frame.columns if column.startswith("Center ")
    ]
    styled = display_frame.style.map(emphasize_target_range, subset=center_columns)
    st.dataframe(styled, hide_index=True, use_container_width=True)
    st.caption(f"Counts from {bold_min} through {bold_max} are bold.")


if st.button("Analyze letter sets", type="primary", disabled=(
    not raw_input.strip() or bold_min > bold_max
)):
    try:
        letter_sets = parse_letter_sets(raw_input)
    except InputIssue as exc:
        st.error(str(exc))
    else:
        progress = st.progress(0.0, text="Starting Chrome…")

        def report_progress(
            done: int, total: int, letter_set: str, center: str
        ) -> None:
            progress.progress(
                done / total,
                text=f"Checking {letter_set} with {center} in the center "
                f"({done}/{total})",
            )

        try:
            results = analyze_letter_sets(
                letter_sets, progress_callback=report_progress
            )
        except Exception as exc:
            progress.empty()
            st.session_state.pop("results", None)
            st.error(f"The SB Solver lookup could not be completed: {exc}")
            st.info(
                "This app requests SB Solver directly through Chrome. If "
                "Cloudflare loops, SB Solver is blocking the automated browser; "
                "the app cannot complete or bypass that challenge."
            )
        else:
            progress.empty()
            st.session_state["results"] = results
            st.success(
                f"Analyzed {len(results)} letter set"
                f"{'s' if len(results) != 1 else ''} across "
                f"{len(results) * 7} center-letter combinations."
            )

if results := st.session_state.get("results"):
    render_results(results)
