"""Offline failure-state checks for the isolated hosting probe."""

import unittest
from unittest.mock import Mock, patch

from selenium.common.exceptions import TimeoutException
from pilot.probe import observe


class PilotTests(unittest.TestCase):
    def browser(self, url, text="Search results"):
        browser = Mock(current_url=url)
        browser.find_element.return_value.text = text
        return browser

    def immediate_wait(self, browser, timeout):
        wait = Mock()

        def until(read):
            result = read(browser)
            if not result:
                raise TimeoutException()
            return result

        wait.until.side_effect = until
        return wait

    @patch("pilot.probe.WebDriverWait")
    def test_challenge_with_stale_table_is_blocked(self, wait):
        browser = self.browser("https://www.sbsolver.com/s/reGicdq", "Verify you are human")
        wait.side_effect = self.immediate_wait
        result = observe(browser, "sbsolver", "reGicdq")
        self.assertEqual(result["status"], "BLOCKED")
        browser.find_elements.assert_not_called()

    @patch("pilot.probe.WebDriverWait")
    def test_wrong_puzzle_does_not_supply_candidates(self, wait):
        browser = self.browser("https://www.sbsolver.com/s/gaiNoqy")
        wait.side_effect = self.immediate_wait
        result = observe(browser, "sbsolver", "reGicdq")
        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertNotIn("words", result)

    @patch("pilot.probe.WebDriverWait")
    def test_missing_result_is_not_confirmed_absence(self, wait):
        browser = self.browser("https://www.oed.com/search/dictionary/?q=DERIG")
        browser.find_elements.return_value = []
        wait.side_effect = self.immediate_wait
        result = observe(browser, "oed", "DERIG")
        self.assertEqual(result["status"], "UNRESOLVED")

    @patch("pilot.probe.WebDriverWait")
    def test_first_result_only_and_missing_frequency_unresolved(self, wait):
        for value, status in (("3", "OBSERVED"), (None, "UNRESOLVED"), ("broken", "UNRESOLVED")):
            with self.subTest(value=value):
                browser = self.browser("https://www.oed.com/search/dictionary/?q=DEGREE")
                first, second = Mock(), Mock()
                def fields(by, name):
                    if name == "frequencyIndicator":
                        return [] if value is None else [Mock(get_attribute=Mock(return_value=value))]
                    return [Mock(text="degree")]
                first.find_elements.side_effect = fields
                browser.find_elements.return_value = [first, second]
                wait.side_effect = self.immediate_wait
                result = observe(browser, "oed", "DEGREE")
                self.assertEqual(result["status"], status)
                second.find_elements.assert_not_called()
                if status == "OBSERVED":
                    self.assertEqual(result["usage_bars"], 3)


if __name__ == "__main__":
    unittest.main()
