from __future__ import annotations

import re
from collections.abc import Callable, Iterable

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


BASE_URL = "https://www.sbsolver.com/s/"
WORD_SELECTOR = "table.bee-set td.bee-hover a"


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


def sbsolver_link(letters: str) -> str:
    # Do not lowercase this—capitalization identifies the center.
    return f"{BASE_URL}{letters}"


def chrome_options() -> Options:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,1000")
    options.page_load_strategy = "eager"
    return options


def fetch_word_count(driver: webdriver.Chrome, letters: str, timeout: int = 12) -> int:
    driver.get(sbsolver_link(letters))
    WebDriverWait(driver, timeout).until(
        lambda current_driver: current_driver.execute_script("return document.readyState")
        in {"interactive", "complete"}
    )
    return len(driver.find_elements(By.CSS_SELECTOR, WORD_SELECTOR))


def analyze_letter_sets(
    letter_sets: Iterable[str],
    progress_callback: Callable[[int, int, str, str], None] | None = None,
) -> list[dict]:
    sets = list(letter_sets)
    total = len(sets) * 7
    done = 0
    results: list[dict] = []

    # One hidden browser is reused for the entire batch. This is much faster than
    # launching Chrome once for each of the seven center-letter permutations.
    driver = webdriver.Chrome(options=chrome_options())
    driver.implicitly_wait(5)
    try:
        for letter_set in sets:
            centers = []
            for center_index, center_letter in enumerate(letter_set):
                ordered_letters = sbsolver_letters(letter_set, center_index)
                count = fetch_word_count(driver, ordered_letters)
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
    finally:
        driver.quit()

    return results
