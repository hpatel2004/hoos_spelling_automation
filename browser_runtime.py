"""Chrome startup for desktop use and Linux hosting."""

import os
import sys

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


def hosted_browser() -> bool:
    return sys.platform.startswith("linux") or os.environ.get("RENDER") == "true" or os.environ.get("HOOS_HEADLESS") == "1"


def create_chrome():
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    if hosted_browser():
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1280,900")
    if os.environ.get("CHROMIUM_BINARY"):
        options.binary_location = os.environ["CHROMIUM_BINARY"]
    kwargs = {"options": options}
    if os.environ.get("CHROMEDRIVER_BINARY"):
        kwargs["service"] = Service(executable_path=os.environ["CHROMEDRIVER_BINARY"])
    try:
        return webdriver.Chrome(**kwargs)
    except WebDriverException as exc:
        raise RuntimeError(
            "Could not start Chromium. On Render, deploy using the repository's "
            "root Dockerfile, which installs Chromium and its matching driver. "
            "A Python-only deploy does not install the required browser."
        ) from exc
