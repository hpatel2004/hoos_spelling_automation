"""Check typography stays inside the actual clipboard/export document."""

import unittest
from unittest.mock import patch

import app
import oed_parser as oed


class CopyOutputTests(unittest.TestCase):
    def test_export_has_inline_document_font_and_preserves_editorial_links(self):
        html = oed.build_output_html(
            [("ONION", "", "")], [("EGER", "", oed.EDITORIAL_EXCLUDED_NOTE)],
            creator="Heer Patel", link="https://www.sbsolver.com/s/aNoyigq",
            puzzle_title="ANOYIG", center_letter="N",
        )
        self.assertIn(f'<div style="{oed.DOCUMENT_STYLE}">', html)
        self.assertIn("font-size: 12pt", html)
        self.assertIn('href="https://www.sbsolver.com/s/aNoyigq"', html)
        self.assertIn('href="https://www.oed.com/search/dictionary/?scope=Entries&amp;q=ONION"', html)
        self.assertIn("<ol>", html)
        self.assertIn('background: yellow;', html)
        with patch.object(app.components, "html") as render:
            app.render_copyable_output(html)
        component = render.call_args.args[0]
        self.assertIn("const copyHtml = fullHtml;", component)
        self.assertIn('"text/html"', component)
        self.assertIn('"text/plain"', component)
        self.assertIn('role="status"', component)
        self.assertIn("if (!copied)", component)
        self.assertIn("press Ctrl+C or Command+C", component)


if __name__ == "__main__":
    unittest.main()
