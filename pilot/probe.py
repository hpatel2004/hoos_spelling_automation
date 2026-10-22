"""Collect bounded, first-result observations. Never solve access challenges."""

import argparse
import json
import os
import time
from datetime import datetime, timezone
from urllib.parse import urlencode, urlsplit

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from sbsolver_parser import WORD_SELECTOR, validate_sbsolver_letters


def observe(driver, provider, query):
    """Return observations, never an editorial acceptance/rejection."""
    url = (f"https://www.sbsolver.com/s/{query}" if provider == "sbsolver"
           else "https://www.oed.com/search/dictionary/?" + urlencode({"scope": "Entries", "q": query}))
    record = {"provider": provider, "query": query, "url": url,
              "status": "UNRESOLVED", "observed_at": datetime.now(timezone.utc).isoformat()}
    started = time.monotonic()
    try:
        driver.get(url)

        def read_page(browser):
            text = browser.find_element(By.TAG_NAME, "body").text.lower()
            if any(marker in text for marker in (
                "verify you are human", "checking your browser", "access denied",
                "just a moment", "verify that you are human", "too many requests",
            )) or "/cdn-cgi/" in browser.current_url:
                return {"status": "BLOCKED"}
            if urlsplit(browser.current_url)._replace(query="", fragment="") != urlsplit(url)._replace(query="", fragment=""):
                return {"status": "UNRESOLVED", "reason": "Unexpected redirect"}
            if provider == "sbsolver":
                words = list(dict.fromkeys(
                    el.text.strip().upper() for el in browser.find_elements(By.CSS_SELECTOR, WORD_SELECTOR)
                    if el.text.strip()
                ))
                if words:
                    return {"status": "OBSERVED", "words": words, "word_count": len(words),
                            "completeness": "Requires comparison with editor reference"}
                return False
            results = browser.find_elements(By.CLASS_NAME, "resultsSetItem")
            if not results:
                return False  # No result selector alone is not proof of no results.
            first = results[0]
            fields = {}
            for name in ("hw", "ps", "snippet"):
                elements = first.find_elements(By.CLASS_NAME, name)
                fields[name] = elements[0].text.strip() if elements else None
            frequencies = first.find_elements(By.CLASS_NAME, "frequencyIndicator")
            value = frequencies[0].get_attribute("aria-valuenow") if frequencies else None
            if not fields["hw"] or value is None or not value.isdigit():
                return False  # Allow delayed fields to load; absence stays unresolved.
            return {"status": "OBSERVED", "first_result": fields, "usage_bars": int(value),
                    "classification": "Not evaluated; compare with editor browser"}

        record.update(WebDriverWait(driver, 20).until(read_page))
    except TimeoutException:
        record.update(status="UNRESOLVED", reason="Timeout or incomplete metadata; absence not confirmed")
    except WebDriverException:
        record.update(status="UNRESOLVED", reason="Browser or navigation failure")
    finally:
        record["duration_seconds"] = round(time.monotonic() - started, 2)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", action="append", required=True, help="Seven SB Solver letters, center uppercase; repeat for each puzzle")
    parser.add_argument("--word", action="append", required=True, help="Representative OED word; repeat as needed")
    parser.add_argument("--host-label", required=True, help="Actual platform/plan/region, or local")
    parser.add_argument("--access-reviewed", action="store_true", help="Applicable source access terms have been reviewed for this run")
    args = parser.parse_args()
    if not args.access_reviewed:
        parser.error("Review source access terms before making pilot requests; then supply --access-reviewed")
    for query in args.query:
        validate_sbsolver_letters(query)
    if len(args.query) > 2 or len(args.word) > 10:
        parser.error("Pilot limited to two puzzles and ten OED words per run")
    options = Options()
    for argument in ("--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--window-size=1280,900"):
        options.add_argument(argument)
    if os.environ.get("CHROMIUM_BINARY"):
        options.binary_location = os.environ["CHROMIUM_BINARY"]
    service = Service(executable_path=os.environ["CHROMEDRIVER_BINARY"]) if os.environ.get("CHROMEDRIVER_BINARY") else Service()
    report = {"host": args.host_label, "gate": "NOT_PASSED_REQUIRES_MANUAL_COMPARISON", "observations": []}
    driver = webdriver.Chrome(options=options, service=service)
    driver.set_page_load_timeout(30)
    try:
        for provider, queries in (("sbsolver", args.query), ("oed", args.word)):
            for query in queries:
                if report["observations"]:
                    time.sleep(7)
                result = observe(driver, provider, query)
                report["observations"].append(result)
                if result["status"] != "OBSERVED":
                    break  # Stop this provider; do not repeatedly request blocked/incomplete pages.
    finally:
        driver.quit()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
