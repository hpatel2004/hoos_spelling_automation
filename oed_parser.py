import streamlit as st
from typing import List, Tuple
import tempfile
import os
import time
import random

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

OED_HOME = "https://www.oed.com/"

# -----------------------------
# OED functions
# -----------------------------
def oed_link(word: str) -> str:
    return f"{OED_HOME}search/dictionary/?scope=Entries&q={word}"

def classify_words(words: List[str]):
    common, rare = [], []
    variant_markers = ["variant of", "also a variant of", "alteration of", "spelling of"]

    # -----------------------------
    # Selenium setup
    # -----------------------------
    options = Options()
    # options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 6)

    for word in words:
        time.sleep(random.uniform(6, 11))
        print(f"Processing {word}...")
        url = oed_link(word)

        try:
            driver.get(url)

            try:
                # ✅ grab the WHOLE result card (matches your HTML exactly)
                result = wait.until(
                    EC.visibility_of_element_located((By.CLASS_NAME, "resultsSetItem"))
                )
            except:
                rare.append((word, f'<a href="{OED_HOME}">{word}</a>', "No results"))
                continue

            # -----------------------------
            # Frequency (WORKS on search page)
            # -----------------------------
            try:
                freq_div = result.find_element(By.CLASS_NAME, "frequencyIndicator")
                usage = int(freq_div.get_attribute("aria-valuenow"))
            except:
                usage = None

            # -----------------------------
            # Snippet (definition preview)
            # -----------------------------
            try:
                snippet = result.find_element(By.CLASS_NAME, "snippet").text.lower()
            except:
                snippet = ""

            # -----------------------------
            # Variant detection
            # -----------------------------
            try:
                ps_text = result.find_element(By.CLASS_NAME, "ps").text.lower()
            except:
                ps_text = ""

            is_variant = "variant of" in ps_text
            # -----------------------------
            # Slang detection
            # -----------------------------
            is_slang = "slang" in snippet

            # -----------------------------
            # Proper noun detection
            # -----------------------------
            try:
                title = result.find_element(By.CLASS_NAME, "hw").text.strip()
                is_proper_noun = title and title[0].isupper()
            except:
                is_proper_noun = False

            # -----------------------------
            # Get REAL entry link
            # -----------------------------
            link = f'<a href="{url}">{word}</a>'

            # -----------------------------
            # CLASSIFICATION
            # -----------------------------
            if is_variant:
                rare.append((word, link, "Variant form"))
            elif is_proper_noun:
                rare.append((word, link, "Proper noun"))
            elif is_slang:
                rare.append((word, link, "Slang"))
            elif usage is None:
                rare.append((word, link, "Missing frequency data"))
            elif usage <= 2:
                rare.append((word, link, f"Low frequency ({usage})"))
            else:
                common.append((word, link, ""))

        except Exception:
            rare.append((word, f'<a href="{OED_HOME}">{word}</a>', "Error fetching"))

    driver.quit()

    # -----------------------------
    # SORTING
    # -----------------------------
    common.sort(key=lambda x: x[0])
    rare.sort(key=lambda x: x[0])

    return common, rare

# hyperlinker 

def add_hyperlink(paragraph, url, text):
    part = paragraph.part
    r_id = part.relate_to(url, RT.HYPERLINK, is_external=True)

    hyperlink = OxmlElement('w:hyperlink')
    hyperlink.set(qn('r:id'), r_id)

    new_run = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')

    # Style (blue + underline)
    u = OxmlElement('w:u')
    u.set(qn('w:val'), 'single')
    rPr.append(u)

    color = OxmlElement('w:color')
    color.set(qn('w:val'), '0000FF')
    rPr.append(color)

    new_run.append(rPr)

    text_elem = OxmlElement('w:t')
    text_elem.text = text
    new_run.append(text_elem)

    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)

    return hyperlink


# doc creator
def create_docx(common, rare, filename="oed_classification.docx"):
    doc = Document()

    doc.add_heading("OED Word Classification", 0)

    # -----------------------------
    # Common Words
    # -----------------------------
    doc.add_heading("Common Words", 1)

    for word, link, reason in common:
        p = doc.add_paragraph()
        add_hyperlink(p, oed_link(word), word)

    # -----------------------------
    # Rare Words
    # -----------------------------
    doc.add_heading("Rare / Excluded Words", 1)

    for word, link, reason in rare:
        p = doc.add_paragraph()
        add_hyperlink(p, oed_link(word), word)
        if reason:
            p.add_run(f" – {reason}")

    doc.save(filename)
    return filename

# -----------------------------
# HTML generator (UNCHANGED)
# -----------------------------
def write_html_file(title: str, items):
    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>{title}</title></head>
<body>
<h2>{title}</h2>
<ul>
"""
    html += "\n".join(
        f"<li>{link} – {reason}</li>" for (_, link, reason) in items
    )
    html += "\n</ul></body></html>"
    return html

# -----------------------------
# Streamlit UI (UNCHANGED)
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

        st.subheader("Common Words")
        for _, link, reason in common:
            st.markdown(f"- {link} ({reason})", unsafe_allow_html=True)

        st.subheader("Rare / Excluded Words")
        for _, link, reason in rare:
            st.markdown(f"- {link} ({reason})", unsafe_allow_html=True)

        common_html = write_html_file("Common Words", common)
        rare_html = write_html_file("Rare / Variant / Missing Words", rare)

        tmp_common = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
        tmp_common.write(common_html.encode("utf-8"))
        tmp_common.close()

        tmp_rare = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
        tmp_rare.write(rare_html.encode("utf-8"))
        tmp_rare.close()

        st.download_button(
            "Download Common Words HTML",
            data=open(tmp_common.name, "rb"),
            file_name="common_words.html"
        )

        st.download_button(
            "Download Rare Words HTML",
            data=open(tmp_rare.name, "rb"),
            file_name="rare_words.html"
        )

        docx_path = create_docx(common, rare)

        with open(docx_path, "rb") as f:
            st.download_button(
                "Download Word Document (.docx)",
                data=f,
                file_name="oed_classification.docx"
            )