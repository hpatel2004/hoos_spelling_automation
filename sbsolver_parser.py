import os
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


def fetch_words_sbsolver(letters: str):
    url = sbsolver_link(letters)

    start_debug_chrome()
    options = Options()
    options.debugger_address = f"127.0.0.1:{DEBUG_PORT}"

    driver = webdriver.Chrome(options=options)

    try:
        driver.get(url)
        driver.implicitly_wait(5)

        try:
            WebDriverWait(driver, 90).until(
                lambda current_driver: current_driver.find_elements(
                    By.CSS_SELECTOR, WORD_SELECTOR
                )
            )
        except TimeoutException:
            raise RuntimeError(
                "SB Solver is showing a Cloudflare security check. "
                "Complete it in the Chrome window that opened, then try again. "
                "You can also paste the word list into Step 2."
            )

        word_elements = driver.find_elements(By.CSS_SELECTOR, WORD_SELECTOR)
        words = [el.text.strip().upper() for el in word_elements if el.text.strip()]
        return words

    finally:
        driver.quit()
