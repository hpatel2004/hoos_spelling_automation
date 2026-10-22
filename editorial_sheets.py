"""Read one-column editorial lists from anonymously readable Google Sheets."""

import csv
import io
import re
import unicodedata
from urllib.error import URLError
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

MAX_BYTES = 2 * 1024 * 1024
MAX_ROWS = 20000


def sheet_csv_url(link: str) -> str:
    parsed = urlsplit(link.strip())
    if (parsed.scheme != "https" or parsed.netloc != "docs.google.com"
            or parsed.username or parsed.password):
        raise ValueError("Use an HTTPS Google Sheets link from docs.google.com.")
    match = re.fullmatch(r"/spreadsheets/d/(e/)?([A-Za-z0-9_-]+)(?:/(?:edit|view|preview|export|pubhtml|pub))?/?", parsed.path)
    if not match:
        raise ValueError("Use a Google Sheets sharing link or published sheet link.")
    published, sheet_id = match.groups()
    query, fragment = parse_qs(parsed.query), parse_qs(parsed.fragment)
    gid = fragment.get("gid", query.get("gid", [None]))[0]
    if gid is not None and not re.fullmatch(r"[0-9]+", gid):
        raise ValueError("The sheet tab ID (gid) must be numeric.")
    params = {"output": "csv", "single": "true"} if published else {"format": "csv"}
    if gid is not None:
        params["gid"] = gid
    if query.get("resourcekey"):
        key = query["resourcekey"][0]
        if not re.fullmatch(r"[A-Za-z0-9_-]+", key):
            raise ValueError("The Google Sheets resource key is invalid.")
        params["resourcekey"] = key
    path = f"e/{sheet_id}/pub" if published else f"{sheet_id}/export"
    return f"https://docs.google.com/spreadsheets/d/{path}?{urlencode(params)}"


class _GoogleOnlyRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urlsplit(newurl)
        host = target.hostname or ""
        if (target.scheme != "https" or target.username or target.password
                or target.port not in (None, 443)
                or not (host == "docs.google.com" or host.endswith(".googleusercontent.com"))):
            raise ValueError("The sheet requires sign-in or redirected outside the supported Google download hosts. Enable public viewing or publish the sheet.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def parse_sheet_csv(data: bytes) -> list[str]:
    if len(data) > MAX_BYTES:
        raise ValueError("The sheet download exceeds the 2 MB limit.")
    try:
        text = data.decode("utf-8-sig")
        if text.lstrip().startswith("<"):
            raise ValueError("Google returned a web page instead of sheet data. Enable public viewing or publish the sheet.")
        words = []
        first_nonempty = True
        for row_number, row in enumerate(csv.reader(io.StringIO(text), strict=True), start=1):
            if row_number > MAX_ROWS:
                raise ValueError("The sheet exceeds the 20,000-row limit.")
            word = unicodedata.normalize("NFC", row[0].strip()).upper() if row else ""
            if not word:
                continue
            is_header = first_nonempty and word in {"WORD", "WORDS"}
            first_nonempty = False
            if is_header:
                continue
            if len(word) > 128 or "\n" in word or "\r" in word:
                raise ValueError(f"Row {row_number}: put one word in each cell of column A.")
            words.append(word)
    except (UnicodeDecodeError, csv.Error) as exc:
        raise ValueError("Could not read the sheet as UTF-8 CSV data.") from exc
    return list(dict.fromkeys(words))


def fetch_google_sheet_words(link: str) -> list[str]:
    url = sheet_csv_url(link)
    request = Request(url, headers={"Accept": "text/csv", "User-Agent": "HoosSpelling/1.0"})
    try:
        with build_opener(_GoogleOnlyRedirects()).open(request, timeout=15) as response:
            if "html" in response.headers.get("Content-Type", "").lower():
                raise ValueError("Google returned a web page instead of sheet data. Enable public viewing or publish the sheet.")
            data = response.read(MAX_BYTES + 1)
    except (URLError, TimeoutError, OSError) as exc:
        raise ValueError("Could not download the Google Sheet. Check its link and allow viewing without sign-in; then load it again.") from exc
    return parse_sheet_csv(data)
