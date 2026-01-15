import requests
from bs4 import BeautifulSoup
from typing import List, Tuple

# -----------------------------
# SB Solver Scraper (requests)
# -----------------------------

BASE_SB_URL = "https://www.sbsolver.com/s/"

def fetch_words_sbsolver(letters: str) -> List[str]:
    """
    Fetches all words from SB Solver for the given letters.
    Returns a list of words in ALL CAPS.
    """
    url = BASE_SB_URL + letters
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Select only words from the table
    word_elements = soup.select("table.bee-set td.bee-hover a")

    words = [el.get_text(strip=True).upper() for el in word_elements if el.get_text(strip=True)]
    return words

# -----------------------------
# OED Frequency & Variant Checker
# -----------------------------

OED_HOME = "https://www.oed.com/"

def oed_link(word: str) -> str:
    return f"{OED_HOME}search/dictionary/?q={word}"

def classify_words(words: List[str]) -> Tuple[List[str], List[str]]:
    """
    Classifies words into common and rare/variant.
    Returns (common, rare) lists of HTML links.
    """
    common, rare = [], []

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    for word in words:
        url = oed_link(word)
        try:
            resp = requests.get(url, headers=headers)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Check for frequency indicator
            freq_div = soup.find(class_="frequencyIndicator")
            if freq_div and freq_div.has_attr("aria-valuenow"):
                usage = int(freq_div["aria-valuenow"])
            else:
                usage = 0  # Treat missing frequency as rare

            # Check for primary variant (first sense)
            variant_markers = ["variant of", "also a variant of", "alteration of", "spelling of"]
            first_def = ""
            first_sense = soup.select_one(".sense, .definition")
            if first_sense:
                first_def = first_sense.get_text(strip=True).lower()
            is_variant = any(marker in first_def for marker in variant_markers)

            link = f'<a href="{url}">{word}</a>'
            if usage <= 2 or is_variant:
                rare.append(link)
            else:
                common.append(link)

        except requests.RequestException:
            # If page not found or network error, treat as rare
            rare.append(f'<a href="{OED_HOME}">{word}</a>')

    return common, rare

# -----------------------------
# HTML Writer
# -----------------------------

def write_html(filename: str, title: str, items: List[str]):
    with open(filename, "w") as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>{title}</title>
</head>
<body>
<h2>{title}</h2>
<ul>
""")
        for item in items:
            f.write(f"<li>{item}</li>\n")
        f.write("""
</ul>
</body>
</html>
""")

# -----------------------------
# Optional CLI Usage
# -----------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Hoos Spelling Puzzle Generator (Requests)")
    parser.add_argument("letters", help="Letter set (e.g. pRincej)")
    args = parser.parse_args()

    words = fetch_words_sbsolver(args.letters)
    print(f"Fetched {len(words)} words from SB Solver.")

    common, rare = classify_words(words)
    print(f"{len(common)} common words, {len(rare)} rare/variant words.")

    write_html("common_words.html", "Common Words", common)
    write_html("rare_words.html", "Rare / Variant / Missing Words", rare)
    print("HTML output generated: common_words.html, rare_words.html")
