"""Offline checks for Sheets URLs, CSV ingestion, and safe loading failures."""

import unittest
from unittest.mock import Mock, patch
from urllib.error import URLError

from editorial_sheets import (
    MAX_BYTES, _GoogleOnlyRedirects, fetch_google_sheet_words,
    parse_sheet_csv, sheet_csv_url,
)


class SheetTests(unittest.TestCase):
    def test_sharing_link_uses_selected_tab_and_defaults_to_first(self):
        self.assertEqual(sheet_csv_url("https://docs.google.com/spreadsheets/d/abc_123/edit?usp=sharing#gid=42"),
                         "https://docs.google.com/spreadsheets/d/abc_123/export?format=csv&gid=42")
        self.assertEqual(sheet_csv_url("https://docs.google.com/spreadsheets/d/abc/edit"),
                         "https://docs.google.com/spreadsheets/d/abc/export?format=csv")

    def test_published_links_and_query_gid_supported(self):
        self.assertEqual(sheet_csv_url("https://docs.google.com/spreadsheets/d/e/2PACX-test/pubhtml?gid=12"),
                         "https://docs.google.com/spreadsheets/d/e/2PACX-test/pub?output=csv&single=true&gid=12")

    def test_non_google_and_invalid_links_rejected_before_network(self):
        for link in ("http://docs.google.com/spreadsheets/d/abc/edit", "https://localhost/a",
                     "https://docs.google.com.evil.com/spreadsheets/d/abc/edit",
                     "https://docs.google.com:443/spreadsheets/d/abc/edit",
                     "https://docs.google.com/spreadsheets/d/abc/edit#gid=oops",
                     "https://docs.google.com/document/d/abc/edit"):
            with self.subTest(link=link), patch("editorial_sheets.build_opener") as opener:
                with self.assertRaises(ValueError):
                    fetch_google_sheet_words(link)
                opener.assert_not_called()

    def test_first_column_bom_blank_header_case_and_duplicates(self):
        data = b'\xef\xbb\xbfWords,Notes\nprince,include\n\n PRICE ,exclude\nprince,duplicate\n'
        self.assertEqual(parse_sheet_csv(data), ["PRINCE", "PRICE"])
        self.assertEqual(parse_sheet_csv(b"ONION\nNONAGON\n"), ["ONION", "NONAGON"])
        self.assertEqual(parse_sheet_csv(b""), [])

    def test_html_invalid_encoding_and_oversized_content_rejected(self):
        for data in (b"<!doctype html><h1>Sign in</h1>", b"\xff", b"x" * (MAX_BYTES + 1), b'"unterminated'):
            with self.subTest(data=data[:30]), self.assertRaises(ValueError):
                parse_sheet_csv(data)

    def test_redirects_cannot_fetch_local_or_signin_pages(self):
        handler = _GoogleOnlyRedirects()
        for target in ("http://docs.google.com/file", "https://127.0.0.1/", "https://accounts.google.com/login", "https://example.com/words.csv"):
            with self.subTest(target=target), self.assertRaises(ValueError):
                handler.redirect_request(None, None, 302, "Found", {}, target)

    @patch("editorial_sheets.build_opener")
    def test_download_is_bounded_and_network_errors_are_actionable(self, opener):
        response = Mock(headers={"Content-Type": "text/csv"})
        response.read.return_value = b"Word\nONION\n"
        opener.return_value.open.return_value.__enter__.return_value = response
        self.assertEqual(fetch_google_sheet_words("https://docs.google.com/spreadsheets/d/abc/edit"), ["ONION"])
        response.read.assert_called_once_with(MAX_BYTES + 1)
        opener.return_value.open.side_effect = URLError("Unavailable")
        with self.assertRaisesRegex(ValueError, "allow viewing without sign-in"):
            fetch_google_sheet_words("https://docs.google.com/spreadsheets/d/abc/edit")


if __name__ == "__main__":
    unittest.main()
