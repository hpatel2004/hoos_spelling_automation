import json
import tempfile

import streamlit as st
import streamlit.components.v1 as components

from oed_parser import (
    apply_editorial_filters,
    apply_wahoowa_override,
    build_output_html,
    calculate_levels,
    classify_words,
    create_docx,
    detect_center_letter,
    parse_word_list,
    split_removed_words,
)
from sbsolver_parser import fetch_words_sbsolver, sbsolver_link


def init_session_state():
    defaults = {
        "puzzle_letters": "",
        "word_list_text": "",
        "classification_results": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_copyable_output(output_html: str):
    body_html = (
        output_html.replace("<!DOCTYPE html>", "")
        .split("</head>", 1)[-1]
        .replace("<body>", "")
        .replace("</body></html>", "")
        .strip()
    )
    escaped_html = json.dumps(output_html)

    components.html(
        f"""
        <div style="font-family: Arial, sans-serif;">
            <button id="copy-btn" style="margin-bottom: 12px; padding: 8px 16px; cursor: pointer;">
                Copy formatted output
            </button>
            <p style="color: #666; font-size: 14px; margin-top: 0;">
                Paste into Google Docs or Word to keep hyperlinks. You can also select text below and copy manually.
            </p>
            <div id="output-content" style="border: 1px solid #ccc; padding: 16px; background: white;">
                {body_html}
            </div>
        </div>
        <script>
        const fullHtml = {escaped_html};

        document.getElementById("copy-btn").addEventListener("click", async () => {{
            const content = document.getElementById("output-content");
            const copyHtml = "<html><body>" + content.innerHTML + "</body></html>";
            const plainText = content.innerText;

            try {{
                await navigator.clipboard.write([
                    new ClipboardItem({{
                        "text/html": new Blob([copyHtml], {{ type: "text/html" }}),
                        "text/plain": new Blob([plainText], {{ type: "text/plain" }}),
                    }}),
                ]);
            }} catch (error) {{
                const range = document.createRange();
                range.selectNodeContents(content);
                const selection = window.getSelection();
                selection.removeAllRanges();
                selection.addRange(range);
                document.execCommand("copy");
                selection.removeAllRanges();
            }}

            const button = document.getElementById("copy-btn");
            const originalText = button.textContent;
            button.textContent = "Copied!";
            setTimeout(() => {{
                button.textContent = originalText;
            }}, 2000);
        }});
        </script>
        """,
        height=720,
        scrolling=True,
    )


def render_step1():
    st.subheader("Step 1: Fetch Words from SB Solver")

    letters = st.text_input(
        "Enter letters (e.g., pRincej)",
        value=st.session_state.puzzle_letters,
        placeholder="pRincej",
    )

    if st.button("Fetch Words", key="fetch_words"):
        if not letters:
            st.error("Enter seven letters first.")
            return

        with st.spinner("Fetching words from SB Solver..."):
            try:
                words = fetch_words_sbsolver(letters)
                if not words:
                    st.error("No words found. Make sure the letters are valid.")
                    return

                st.session_state.puzzle_letters = letters
                st.session_state.word_list_text = "\n".join(words)
                st.session_state.classification_results = None
                st.success(f"Fetched {len(words)} words.")
            except Exception as e:
                st.error(f"Error fetching words: {e}")
                return

    if st.session_state.word_list_text:
        st.text_area(
            "Word list (automatically shared with Step 2)",
            value=st.session_state.word_list_text,
            height=400,
        )
        st.code(st.session_state.word_list_text, language=None)


def run_classification(
    word_list_text: str,
    creator: str,
    wahoowa_override: int,
    editorial_included_text: str,
    editorial_excluded_text: str,
):
    words = parse_word_list(word_list_text)
    editorial_included = parse_word_list(editorial_included_text)
    editorial_excluded = parse_word_list(editorial_excluded_text)

    common, rare = classify_words(words)
    common, rare = apply_editorial_filters(
        common, rare, editorial_included, editorial_excluded
    )

    center_letter = detect_center_letter([word for word, _, _ in common])
    word_list = [word for word, _, _ in common]
    levels = calculate_levels(len(word_list), word_list)
    levels = apply_wahoowa_override(
        levels,
        wahoowa_override if wahoowa_override > 0 else None,
    )

    return {
        "common": common,
        "rare": rare,
        "center_letter": center_letter,
        "levels": levels,
        "creator": creator,
    }


def render_classification_results(results: dict):
    puzzle_letters = st.session_state.puzzle_letters
    puzzle_title = puzzle_letters.upper()
    puzzle_link = sbsolver_link(puzzle_letters) if puzzle_letters else ""

    common = results["common"]
    rare = results["rare"]
    center_letter = results["center_letter"]
    levels = results["levels"]
    creator = results["creator"]

    output_html = build_output_html(
        common,
        rare,
        creator=creator,
        link=puzzle_link,
        levels=levels,
        puzzle_title=puzzle_title,
        center_letter=center_letter,
    )

    st.subheader("Copyable output")
    render_copyable_output(output_html)

    docx_filename = f"{puzzle_title}.docx" if puzzle_title else "oed_classification.docx"
    docx_path = create_docx(
        common,
        rare,
        filename=docx_filename,
        creator=creator,
        link=puzzle_link,
        levels=levels,
        puzzle_title=puzzle_title,
    )

    st.download_button(
        "Download formatted HTML",
        data=output_html.encode("utf-8"),
        file_name=f"{puzzle_title or 'oed_classification'}.html",
        mime="text/html",
    )

    with open(docx_path, "rb") as f:
        st.download_button(
            "Download Word Document (.docx)",
            data=f,
            file_name=docx_filename,
        )


def render_step2():
    st.subheader("Step 2: OED Classification")

    puzzle_letters = st.session_state.puzzle_letters
    puzzle_title = puzzle_letters.upper()
    puzzle_link = sbsolver_link(puzzle_letters) if puzzle_letters else ""

    if puzzle_letters:
        st.info(f"Puzzle letters: **{puzzle_title}**")
        st.caption(f"SB Solver link: {puzzle_link}")
    else:
        st.warning("Enter letters in Step 1 first to auto-fill the puzzle title and link.")

    word_list_text = st.text_area(
        "Word list (one word per line)",
        value=st.session_state.word_list_text,
        height=300,
        placeholder="AERATE\nARETE\nARTERY\n...",
        key="step2_word_list",
    )
    st.session_state.word_list_text = word_list_text

    with st.expander("Optional: Puzzle metadata"):
        creator = st.text_input("Creator", placeholder="Heer Patel")
        wahoowa_override = st.number_input(
            "Wahoowa (optional override)",
            min_value=0,
            value=0,
            help=(
                "Count how many words in the final list you easily know. "
                "Leave at 0 to auto-estimate from shorter words (4-6 letters)."
            ),
        )

    with st.expander("Optional: Editorial word filters"):
        editorial_included_text = st.text_area(
            "Editorially included words (one per line)",
            height=150,
            placeholder="Override OED rejections: move these words into Words",
        )
        editorial_excluded_text = st.text_area(
            "Editorially excluded words (one per line)",
            height=150,
            placeholder="Override OED approvals: move these words into Removed Words",
        )

    if not word_list_text.strip():
        return

    words = parse_word_list(word_list_text)
    st.write(f"Loaded {len(words)} words for classification.")

    if st.button("Classify Words", key="classify_words"):
        with st.spinner("Querying OED and classifying words..."):
            st.session_state.classification_results = run_classification(
                word_list_text,
                creator,
                wahoowa_override,
                editorial_included_text,
                editorial_excluded_text,
            )

    if st.session_state.classification_results:
        render_classification_results(st.session_state.classification_results)


def main():
    st.set_page_config(page_title="Hoos Spelling Puzzle Generator", layout="wide")
    init_session_state()

    st.title("Hoos Spelling Puzzle Generator")

    step1_tab, step2_tab = st.tabs(["Step 1: SB Solver", "Step 2: OED Classification"])

    with step1_tab:
        render_step1()

    with step2_tab:
        render_step2()


if __name__ == "__main__":
    main()
