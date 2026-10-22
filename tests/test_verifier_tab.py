"""Main-app integration of the existing automatic verifier, offline."""

import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


def control(items, key):
    return next(item for item in items if item.key == key)


class VerifierTabTests(unittest.TestCase):
    def test_main_app_explains_verifier_without_fetching_on_load(self):
        with patch("verify.verifier.analyze_letter_sets") as analyze:
            at = AppTest.from_file("app.py").run()
            self.assertFalse(at.exception)
            self.assertEqual(at.tabs[2].label, "Verifier")
            self.assertTrue(any("before OED" in item.value for item in at.caption))
            self.assertTrue(any("may fail on Render" in item.value for item in at.info))
            self.assertTrue(control(at.button, "verifier_analyze").disabled)
            analyze.assert_not_called()

    def test_verifier_click_preserves_puzzle_state_and_input_changes_clear_matrix(self):
        matrix = [{"letter_set": "PLANETS", "centers": [
            {"letter": letter, "count": index + 35, "query": letter}
            for index, letter in enumerate("PLANETS")
        ]}]
        with patch("verify.verifier.analyze_letter_sets", return_value=matrix) as analyze:
            at = AppTest.from_file("app.py").run()
            at.text_input[0].set_value("aNoyigq").run()
            at.session_state["word_list_text"] = "ANNOYING\nONION"
            control(at.text_area, "verifier_letters").set_value("PLANETS").run()
            analyze.assert_not_called()
            control(at.button, "verifier_analyze").click().run()
            self.assertFalse(at.exception)
            self.assertEqual(analyze.call_args.args[0], ["PLANETS"])
            self.assertEqual(at.session_state["verifier_results"], matrix)
            self.assertEqual(at.session_state["puzzle_letters"], "aNoyigq")
            self.assertEqual(at.session_state["word_list_text"], "ANNOYING\nONION")
            self.assertEqual(len(at.dataframe), 1)
            control(at.text_area, "verifier_letters").set_value("ORCHIDS").run()
            self.assertNotIn("verifier_results", at.session_state)
            self.assertEqual(len(at.dataframe), 0)

    def test_failed_lookup_clears_only_verifier_results(self):
        with patch("verify.verifier.analyze_letter_sets", side_effect=RuntimeError("Access challenged")):
            at = AppTest.from_file("app.py").run()
            control(at.text_area, "verifier_letters").set_value("PLANETS").run()
            at.session_state["verifier_results"] = [{"letter_set": "PLANETS", "centers": []}]
            control(at.button, "verifier_analyze").click().run()
            self.assertFalse(at.exception)
            self.assertNotIn("verifier_results", at.session_state)
            self.assertTrue(any("Access challenged" in item.value for item in at.error))


if __name__ == "__main__":
    unittest.main()
