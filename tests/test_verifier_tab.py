"""The hosted app exposes only the supported import-and-classify workflow."""

import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


class EditorTabsTests(unittest.TestCase):
    def test_main_app_has_only_supported_tabs_and_no_automatic_sbsolver_requests(self):
        with patch("sbsolver_parser.fetch_words_sbsolver") as fetch:
            at = AppTest.from_file("app.py").run()
            self.assertFalse(at.exception)
            self.assertEqual([tab.label for tab in at.tabs], [
                "Step 1: Import SB Solver", "Step 2: OED Classification",
            ])
            self.assertFalse(any(item.key in {"verifier_analyze", "fetch_sbsolver"} for item in at.button))
            self.assertFalse(any(item.key == "verifier_letters" for item in at.text_area))
            fetch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
