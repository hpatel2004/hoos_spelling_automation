import os
import re
import subprocess
import time
import urllib.request
from urllib.error import URLError

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = "https://www.sbsolver.com/s/"
WORD_SELECTOR = "table.bee-set td.bee-hover a"
DEBUG_PORT = 9222
CHROME_PROFILE = os.path.expanduser("~/.hoos_spelling_chrome")
_pending_verification_letters: str | None = None


def sbsolver_link(letters: str) -> str:
    return f"{BASE_URL}{letters}"


def start_debug_chrome() -> None:
    try:
        urllib.request.urlopen(
            f"http://127.0.0.1:{DEBUG_PORT}/json/version", timeout=1
        ).close()
        return
    except (OSError, URLError):
        pass

    subprocess.Popen(
        [
            "open",
            "-na",
            "Google Chrome",
            "--args",
            f"--remote-debugging-port={DEBUG_PORT}",
            f"--user-data-dir={CHROME_PROFILE}",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(
                f"http://127.0.0.1:{DEBUG_PORT}/json/version", timeout=1
            ).close()
            return
        except (OSError, URLError):
            time.sleep(0.25)

    raise RuntimeError("Could not start the Chrome browser used by SB Solver.")


def validate_sbsolver_letters(letters: str) -> None:
    if (
        not re.fullmatch(r"[A-Za-z]{7}", letters)
        or sum(letter.isupper() for letter in letters) != 1
        or len(set(letters.lower())) != 7
    ):
        raise ValueError(
            "Enter seven different letters with the center letter uppercase "
            "and the other six lowercase."
        )


def fetch_words_sbsolver(letters: str):
    global _pending_verification_letters

    validate_sbsolver_letters(letters)
    url = sbsolver_link(letters)

    start_debug_chrome()
    options = Options()
    options.debugger_address = f"127.0.0.1:{DEBUG_PORT}"

    driver = webdriver.Chrome(options=options)
    keep_browser_open = False

    try:
        current_url = driver.current_url
        resuming_verification = (
            _pending_verification_letters == letters
            and current_url.startswith("https://www.sbsolver.com/cdn-cgi/")
        )
        if not resuming_verification and current_url.rstrip("/") != url.rstrip("/"):
            _pending_verification_letters = None
            driver.get(url)
        driver.implicitly_wait(5)

        try:
            WebDriverWait(driver, 90).until(
                lambda current_driver: current_driver.find_elements(
                    By.CSS_SELECTOR, WORD_SELECTOR
                )
            )
        except TimeoutException:
            keep_browser_open = True
            _pending_verification_letters = letters
            raise RuntimeError(
                "SB Solver did not provide a word list within 90 seconds. "
                "If its security checkbox keeps repeating, open the puzzle "
                "using the normal-browser link in Step 1 and paste the SB "
                "Solver word list below. Repeated automatic retries may not "
                "complete verification."
            )

        word_elements = driver.find_elements(By.CSS_SELECTOR, WORD_SELECTOR)
        words = list(
            dict.fromkeys(
                el.text.strip().upper()
                for el in word_elements
                if el.text.strip()
            )
        )
        if not words:
            raise RuntimeError("SB Solver loaded, but no readable words were found.")
        _pending_verification_letters = None
        return words

    finally:
        if keep_browser_open:
            driver.service.stop()
        else:
            driver.quit()
