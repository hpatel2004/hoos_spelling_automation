"""Extract the same SB Solver word links from a saved HTML page, offline."""

import re
from html.parser import HTMLParser


VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}


class _SBWordParser(HTMLParser):
    """Match table.bee-set td.bee-hover a without executing page scripts."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.words = []

    def handle_starttag(self, tag, attrs):
        if tag in VOID_ELEMENTS:
            return
        attributes = dict(attrs)
        classes = (attributes.get("class") or "").split()
        parent = self.stack[-1] if self.stack else {}
        in_table = parent.get("in_table", False) or (
            tag == "table" and "bee-set" in classes
        )
        in_cell = parent.get("in_cell", False) or (
            tag == "td" and in_table and "bee-hover" in classes
        )
        self.stack.append({
            "tag": tag,
            "in_table": in_table,
            "in_cell": in_cell,
            "parts": [] if tag == "a" and in_cell else None,
        })

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_data(self, data):
        for frame in self.stack:
            if frame["parts"] is not None:
                frame["parts"].append(data)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index]["tag"] == tag:
                for frame in self.stack[index:]:
                    if frame["parts"] is not None:
                        word = "".join(frame["parts"]).strip().upper()
                        if word:
                            self.words.append(word)
                del self.stack[index:]
                break


def parse_saved_sbsolver_page(page: bytes) -> list[str]:
    """Return word labels only, in source order, with duplicates removed."""
    try:
        text = page.decode("utf-8-sig")
    except UnicodeDecodeError:
        declared = re.search(
            rb"<meta\b[^>]*charset\s*=\s*[\"']?\s*([A-Za-z0-9._-]+)",
            page[:8192],
            re.IGNORECASE,
        )
        encoding = declared.group(1).decode("ascii").lower() if declared else ""
        if encoding not in {"iso-8859-1", "latin-1", "windows-1252"}:
            raise ValueError(
                "Could not read the saved page. Save it from Chrome as an HTML "
                "file after the SB Solver word list has loaded."
            ) from None
        text = page.decode(encoding)

    parser = _SBWordParser()
    parser.feed(text)
    parser.close()
    words = list(dict.fromkeys(parser.words))
    if not words:
        raise ValueError(
            "No SB Solver word table was found in this file. Save the puzzle "
            "page after verification finishes and the word list is visible."
        )
    return words
