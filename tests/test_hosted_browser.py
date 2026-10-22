"""Hosted startup and acquisition checks without live provider requests."""

import os
import unittest
from unittest.mock import Mock, patch

from selenium.common.exceptions import TimeoutException, WebDriverException

import browser_runtime
import sbsolver_parser as solver


class BrowserRuntimeTests(unittest.TestCase):
    @patch.dict(os.environ, {"RENDER": "true", "CHROMIUM_BINARY": "/usr/bin/chromium", "CHROMEDRIVER_BINARY": "/usr/bin/chromedriver"})
    @patch("browser_runtime.Service")
    @patch("browser_runtime.webdriver.Chrome")
    def test_render_uses_headless_and_installed_driver(self, chrome, service):
        browser_runtime.create_chrome()
        kwargs = chrome.call_args.kwargs
        self.assertIn("--headless=new", kwargs["options"].arguments)
        self.assertEqual(kwargs["options"].binary_location, "/usr/bin/chromium")
        service.assert_called_once_with(executable_path="/usr/bin/chromedriver")
        self.assertIs(kwargs["service"], service.return_value)
        self.assertFalse(kwargs["options"].debugger_address)

    @patch("browser_runtime.webdriver.Chrome", side_effect=WebDriverException("missing browser"))
    def test_missing_browser_explains_docker_requirement(self, chrome):
        with self.assertRaisesRegex(RuntimeError, "root Dockerfile"):
            browser_runtime.create_chrome()


class HostedSolverTests(unittest.TestCase):
    def run_fetch(self, browser, letters="reGicdq"):
        def wait(driver, timeout):
            def until(read):
                result = read(driver)
                if not result:
                    raise TimeoutException()
                return result
            return Mock(until=until)
        with patch.object(solver, "hosted_browser", return_value=True), patch.object(solver, "create_chrome", return_value=browser), patch.object(solver, "WebDriverWait", side_effect=wait), patch.object(solver, "start_debug_chrome") as desktop:
            try:
                return solver.fetch_words_sbsolver(letters)
            finally:
                desktop.assert_not_called()

    def browser(self, text="Puzzle", url="https://www.sbsolver.com/s/reGicdq"):
        browser = Mock(current_url=url)
        browser.find_element.return_value.text = text
        browser.find_elements.return_value = [Mock(text="DEGREE"), Mock(text="degree"), Mock(text="REGICIDE")]
        return browser

    def test_reads_source_words_and_closes_browser(self):
        browser = self.browser()
        self.assertEqual(self.run_fetch(browser), ["DEGREE", "REGICIDE"])
        browser.get.assert_called_once_with("https://www.sbsolver.com/s/reGicdq")
        browser.quit.assert_called_once()

    def test_challenge_cannot_be_mistaken_for_words(self):
        browser = self.browser(text="Verify you are human")
        with self.assertRaisesRegex(RuntimeError, "blocked or challenged"):
            self.run_fetch(browser)
        browser.find_elements.assert_not_called()
        browser.quit.assert_called_once()

    def test_wrong_puzzle_rejected(self):
        browser = self.browser(url="https://www.sbsolver.com/s/gaiNoqy")
        with self.assertRaisesRegex(RuntimeError, "different page"):
            self.run_fetch(browser)
        browser.quit.assert_called_once()

    def test_timeout_does_not_leave_browser_or_lock(self):
        browser = self.browser()
        browser.get.side_effect = TimeoutException()
        with self.assertRaisesRegex(RuntimeError, "hosted timeout"):
            self.run_fetch(browser)
        browser.quit.assert_called_once()
        self.assertFalse(solver._hosted_fetch_lock.locked())

    def test_failed_startup_releases_lock(self):
        with patch.object(solver, "create_chrome", side_effect=RuntimeError("startup failed")):
            with self.assertRaisesRegex(RuntimeError, "startup failed"):
                solver._fetch_hosted_words("reGicdq")
        self.assertFalse(solver._hosted_fetch_lock.locked())

    def test_concurrent_fetch_does_not_start_browser(self):
        solver._hosted_fetch_lock.acquire()
        try:
            with patch.object(solver, "create_chrome") as create:
                with self.assertRaisesRegex(RuntimeError, "Another SB Solver fetch"):
                    solver._fetch_hosted_words("reGicdq")
                create.assert_not_called()
        finally:
            solver._hosted_fetch_lock.release()


if __name__ == "__main__":
    unittest.main()
