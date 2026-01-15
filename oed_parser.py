import streamlit as st
from bs4 import BeautifulSoup
import requests
from typing import List, Tuple
import tempfile
import os

OED_HOME = "https://www.oed.com/"

# -----------------------------
# OED functions
# -----------------------------
def oed_link(word: str) -> str:
    return f"{OED_HOME}search/dictionary/?q={word}"

def classify_words(words: List[str]) -> Tuple[List[str], List[str]]:
    """
    Classifies words into common and rare/variant.
    Returns (common, rare) lists of HTML links.
    """
    common, rare = [], []
    headers = {"User-Agent": "Mozilla/5.0"}
    variant_markers = ["variant of", "also a variant of", "alteration of", "spelling of"]

    for word in words:
        url = oed_link(word)
        try:
            resp = requests.get(url, headers=headers)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Frequency
            freq_div = soup.find(class_="frequencyIndicator")
            usage = int(freq_div["aria-valuenow"]) if freq_div and freq_div.has_attr("aria-valuenow") else 0

            # Primary variant
            first_sense = soup.select_one(".sense, .definition")
            first_def = first_sense.get_text(strip=True).lower() if first_sense else ""
            is_variant = any(marker in first_def for marker in variant_markers)

            link = f'<a href="{url}">{word}</a>'
            if usage <= 2 or is_variant:
                rare.append(link)
            else:
                common.append(link)

        except requests.RequestException:
            rare.append(f'<a href="{OED_HOME}">{word}</a>')

    return common, rare

def write_html_file(title: str, items: List[str]) -> str:
    """
    Generates HTML content as a string (no file yet)
    """
    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>{title}</title></head>
<body>
<h2>{title}</h2>
<ul>
"""
    html += "\n".join(f"<li>{item}</li>" for item in items)
    html += "\n</ul></body></html>"
    return html

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Hoos Spelling Puzzle - OED Linker")
st.title("Step 2: OED Classification")

uploaded_file = st.file_uploader("Upload reviewed word list (TXT)", type=["txt"])

if uploaded_file is not None:
    words = [line.strip() for line in uploaded_file.read().decode("utf-8").splitlines() if line.strip()]
    st.write(f"Loaded {len(words)} words for classification.")

    if st.button("Classify Words"):
        with st.spinner("Querying OED and classifying words..."):
            common, rare = classify_words(words)
            st.success(f"Done! {len(common)} common, {len(rare)} rare/variant.")

            # Display counts
            st.write(f"Common Words: {len(common)}")
            st.write(f"Rare / Variant / Missing Words: {len(rare)}")

            # Generate HTML and provide download buttons
            common_html = write_html_file("Common Words", common)
            rare_html = write_html_file("Rare / Variant / Missing Words", rare)

            # Save temporary files
            tmp_common = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
            tmp_common.write(common_html.encode("utf-8"))
            tmp_common.close()

            tmp_rare = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
            tmp_rare.write(rare_html.encode("utf-8"))
            tmp_rare.close()

            st.download_button("Download Common Words HTML", data=open(tmp_common.name, "rb"), file_name="common_words.html")
            st.download_button("Download Rare Words HTML", data=open(tmp_rare.name, "rb"), file_name="rare_words.html")
