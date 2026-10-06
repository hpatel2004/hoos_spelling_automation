"""Offline regression checks; no Chrome launches or live dictionary requests."""

from io import BytesIO
from tempfile import NamedTemporaryFile
import unittest
from unittest.mock import Mock, patch

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from streamlit.testing.v1 import AppTest

import app
import oed_parser as oed
from sbsolver_import import parse_saved_sbsolver_page
from sbsolver_parser import validate_sbsolver_letters


SAVED_PAGE = b'''<!doctype html><html><head><meta charset="utf-8"></head><body>
<a href="/about">ABOUT</a>
<table class="statistics"><td class="bee-hover"><a>IGNORE</a></td></table>
<table class="bee-set extra"><tr>
<td class="bee-hover"><a href="/w/rice">rice</a></td>
<td class="other"><a>IGNORE</a></td>
<td class="bee-hover"><span><a href="/w/prince"><b>PRI</b>NCE</a></span></td>
<td class="bee-hover"><a href="/w/rice">RICE</a></td>
<td class="bee-hover"><a href="/w/price">PRICE</a><span>999 points</span></td>
</tr></table>
<script>window.fake = '<table class="bee-set"><td class="bee-hover"><a>FAKE</a>';</script>
</body></html>'''


def first_result(title="word", frequency="3", snippet="Definition.", ps="noun"):
    fields = {"hw": Mock(text=title), "snippet": Mock(text=snippet), "ps": Mock(text=ps)}
    if frequency is not None:
        fields["frequencyIndicator"] = Mock(get_attribute=Mock(return_value=frequency))

    def find(by, name):
        if name not in fields:
            raise NoSuchElementException(name)
        return fields[name]

    result = Mock()
    result.find_element.side_effect = find
    return result


def button(at, key):
    return next(item for item in at.button if item.key == key)


def word_editor(at, key):
    return next(item for item in at.text_area if item.key == key)


class SavedPageTests(unittest.TestCase):
    def test_only_word_table_links_are_imported_in_source_order(self):
        self.assertEqual(parse_saved_sbsolver_page(SAVED_PAGE), ["RICE", "PRINCE", "PRICE"])

    def test_encodings_and_entities_preserve_word_labels(self):
        self.assertEqual(parse_saved_sbsolver_page(b"\xef\xbb\xbf" + SAVED_PAGE), ["RICE", "PRINCE", "PRICE"])
        entity = '<table class="bee-set"><td class="bee-hover"><a>caf&eacute;</a></td></table>'
        self.assertEqual(parse_saved_sbsolver_page(entity.encode()), ["CAFÉ"])
        latin = '<meta charset="iso-8859-1">' + entity.replace("&eacute;", "é")
        self.assertEqual(parse_saved_sbsolver_page(latin.encode("latin-1")), ["CAFÉ"])

    def test_incomplete_or_challenge_pages_are_not_word_lists(self):
        for page in (b"", b"<h1>Verify you are human</h1>", b"<a>RICE</a>", b"\xff"):
            with self.subTest(page=page), self.assertRaises(ValueError):
                parse_saved_sbsolver_page(page)


class EditorialPolicyTests(unittest.TestCase):
    def test_two_vs_three_usage_bars(self):
        for frequency, expected in (("2", ("rare", "Low frequency (2)")), ("3", ("common", "")), (None, ("rare", "Missing frequency data"))):
            with self.subTest(frequency=frequency):
                bucket, _, reason = oed._classify_oed_result("WORD", first_result(frequency=frequency), oed.oed_link("WORD"))
                self.assertEqual((bucket, reason), expected)

    def test_existing_first_result_exclusions(self):
        cases = [
            ({"title": "Prince"}, "Proper noun"),
            ({"title": "co-op"}, "Hyphenated form"),
            ({"title": "café"}, "Accented form"),
            ({"snippet": "a slang term"}, "Slang"),
            ({"ps": "variant of another word"}, "Variant form"),
        ]
        for fields, expected in cases:
            with self.subTest(fields=fields):
                bucket, _, reason = oed._classify_oed_result("WORD", first_result(**fields), oed.oed_link("WORD"))
                self.assertEqual((bucket, reason), ("rare", expected))

    def test_final_overrides_preserve_candidates_and_exclusion_wins(self):
        accepted = [("RICE", "", ""), ("PRICE", "", "")]
        rejected = [("PRINCE", "", "Low frequency (2)")]
        with patch.object(app, "classify_words", return_value=(accepted, rejected)) as lookup:
            output = app.run_classification("RICE\nPRICE\nPRINCE", "", 0, "PRINCE\nPRICE\nABSENT", "PRICE")
        lookup.assert_called_once_with(["RICE", "PRICE", "PRINCE"], progress_callback=None)
        self.assertEqual(output["common"], [("PRINCE", "", oed.EDITORIAL_INCLUDED_NOTE), ("RICE", "", "")])
        self.assertEqual(output["rare"], [("PRICE", "", oed.EDITORIAL_EXCLUDED_NOTE)])
        self.assertEqual(output["levels"]["wahoo_wow"], 2)

    def test_editorial_uploads_are_optional_and_support_utf8_bom(self):
        self.assertEqual(app.combine_editorial_word_lists("RICE", None), "RICE")
        self.assertEqual(app.combine_editorial_word_lists("RICE", BytesIO(b"\xef\xbb\xbfprice\r\n")), "RICE\nprice")
        with self.assertRaises(UnicodeDecodeError):
            app.combine_editorial_word_lists("", BytesIO(b"\xff"))


class BrowserWorkflowTests(unittest.TestCase):
    def test_progress_and_cleanup_preserve_existing_timeout_behavior(self):
        browser = Mock()
        browser.get.side_effect = [None, None, RuntimeError("Navigation failed")]
        wait = Mock()
        wait.until.side_effect = [first_result(title="rice"), TimeoutException()]
        events = []
        with patch.object(oed.webdriver, "Chrome", return_value=browser), patch.object(oed, "WebDriverWait", return_value=wait), patch.object(oed.time, "sleep"):
            accepted, rejected = oed.classify_words(["RICE", "PRICE", "PRINCE", "CO-OP"], progress_callback=lambda *event: events.append(event))
        self.assertEqual([word for word, _, _ in accepted], ["RICE"])
        self.assertEqual({word: reason for word, _, reason in rejected}, {"PRICE": "No results", "PRINCE": "Error fetching", "CO-OP": "Contains hyphen"})
        self.assertEqual(events[0], (0, 4, ""))
        self.assertEqual(events[-1], (4, 4, "CO-OP"))
        self.assertEqual([done for done, _, _ in events], sorted(done for done, _, _ in events))
        browser.quit.assert_called_once()

    def test_empty_input_does_not_launch_chrome(self):
        with patch.object(oed.webdriver, "Chrome") as launch:
            self.assertEqual(oed.classify_words([]), ([], []))
        launch.assert_not_called()

    def test_variable_placeholder_queries_retain_existing_validation(self):
        for letters in ("pRinceq", "pRincej", "Planetq"):
            validate_sbsolver_letters(letters)
        for letters in ("", "PRINCEQ", "princeq", "pRincee", "pRince", "../test"):
            with self.subTest(letters=letters), self.assertRaises(ValueError):
                validate_sbsolver_letters(letters)


class StreamlitWorkflowTests(unittest.TestCase):
    def test_saved_import_editorial_uploads_progress_and_synchronization(self):
        uploads = {
            "sbsolver_saved_page": BytesIO(SAVED_PAGE),
            "editorial_included_file": BytesIO(b"\xef\xbb\xbfprince\nABSENT"),
            "editorial_excluded_file": BytesIO(b"price\n"),
        }

        def upload(label, **kwargs):
            return uploads[kwargs["key"]]

        def classify(words, progress_callback=None):
            self.assertEqual(words, ["RICE", "PRINCE", "PRICE"])
            for done, word in enumerate(words, start=1):
                progress_callback(done, len(words), word)
            return [("RICE", "", ""), ("PRICE", "", "")], [("PRINCE", "", "Low frequency (2)")]

        with NamedTemporaryFile(suffix=".docx") as export:
            export.write(b"mocked export")
            export.flush()
            with patch("streamlit.file_uploader", side_effect=upload), patch("sbsolver_parser.fetch_words_sbsolver") as fetch, patch("oed_parser.classify_words", side_effect=classify), patch("oed_parser.create_docx", return_value=export.name):
                at = AppTest.from_file("app.py").run()
                self.assertTrue(button(at, "import_saved_sbsolver").disabled)
                at.text_input[0].set_value("pRinceq").run()
                button(at, "import_saved_sbsolver").click().run()
                self.assertFalse(at.exception)
                self.assertEqual(word_editor(at, "step1_word_list").value, "RICE\nPRINCE\nPRICE")
                self.assertEqual(word_editor(at, "step2_word_list").value, "RICE\nPRINCE\nPRICE")
                fetch.assert_not_called()
                button(at, "classify_words").click().run()
                self.assertFalse(at.exception)
                self.assertEqual(at.get("progress")[0].proto.value, 100)
                results = at.session_state["classification_results"]
                self.assertEqual([word for word, _, _ in results["common"]], ["PRINCE", "RICE"])
                self.assertEqual([word for word, _, _ in results["rare"]], ["PRICE"])
                word_editor(at, "step2_word_list").set_value("RICE").run()
                self.assertEqual(word_editor(at, "step1_word_list").value, "RICE")
                self.assertIsNone(at.session_state["classification_results"])
                uploads["sbsolver_saved_page"] = BytesIO(b"<h1>Verify you are human</h1>")
                at.run()
                button(at, "import_saved_sbsolver").click().run()
                self.assertTrue(any("No SB Solver word table" in error.value for error in at.error))
                self.assertEqual(word_editor(at, "step2_word_list").value, "RICE")
                uploads["editorial_included_file"] = BytesIO(b"\xff")
                at.run()
                self.assertTrue(button(at, "classify_words").disabled)
                at.text_input[0].set_value("Planetq").run()
                self.assertEqual(word_editor(at, "step1_word_list").value, "")
                self.assertEqual(word_editor(at, "step2_word_list").value, "")
                self.assertFalse(at.exception)


if __name__ == "__main__":
    unittest.main()
