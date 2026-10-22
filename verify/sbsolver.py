from __future__ import annotations

import re
from collections.abc import Callable, Iterable

from sbsolver_parser import fetch_words_sbsolver


class InputIssue(ValueError):
    """Raised when one or more submitted letter sets are invalid."""


def parse_letter_sets(raw_input: str) -> list[str]:
    candidates = [item.upper() for item in re.findall(r"[A-Za-z]+", raw_input)]
    if not candidates:
        raise InputIssue("Enter at least one seven-letter set.")

    invalid = [item for item in candidates if len(item) != 7 or len(set(item)) != 7]
    if invalid:
        examples = ", ".join(invalid[:5])
        suffix = "…" if len(invalid) > 5 else ""
        raise InputIssue(
            "Every entry must contain exactly seven different letters. "
            f"Please fix: {examples}{suffix}"
        )

    # Avoid repeating network work when an entry appears more than once.
    return list(dict.fromkeys(candidates))


def sbsolver_letters(letter_set: str, center_index: int) -> str:
    center = letter_set[center_index].upper()
    optional = (
        letter_set[:center_index]
        + letter_set[center_index + 1:]
    ).lower()

    return center + optional


def fetch_word_count(letters: str) -> int:
    return len(fetch_words_sbsolver(letters))


def analyze_letter_sets(
    letter_sets: Iterable[str],
    progress_callback: Callable[[int, int, str, str], None] | None = None,
) -> list[dict]:
    sets = list(letter_sets)
    total = len(sets) * 7
    done = 0
    results: list[dict] = []

    for letter_set in sets:
        centers = []
        for center_index, center_letter in enumerate(letter_set):
            ordered_letters = sbsolver_letters(letter_set, center_index)
            count = fetch_word_count(ordered_letters)
            centers.append(
                {
                    "letter": center_letter,
                    "count": count,
                    "query": ordered_letters,
                }
            )
            done += 1
            if progress_callback:
                progress_callback(done, total, letter_set, center_letter)
        results.append({"letter_set": letter_set, "centers": centers})

    return results
