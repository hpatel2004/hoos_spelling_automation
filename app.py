import json

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
from sbsolver_parser import (
    fetch_words_sbsolver,
    sbsolver_link,
    validate_sbsolver_letters,
)
from sbsolver_import import parse_saved_sbsolver_page


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


def set_word_list(text: str):
    st.session_state.word_list_text = text
    st.session_state.step1_word_list = text
    st.session_state.step2_word_list = text
    st.session_state.classification_results = None


def sync_word_list(source_key: str):
    set_word_list(st.session_state[source_key])


def render_step1():
    st.subheader("Step 1: Fetch Words from SB Solver")

    if "puzzle_letters_input" not in st.session_state:
        st.session_state.puzzle_letters_input = st.session_state.puzzle_letters
    letters = st.text_input(
        "Six puzzle letters plus a placeholder (uppercase center)",
        key="puzzle_letters_input",
        placeholder="pRincej",
    ).strip()

    valid_letters = False
    if letters:
        try:
            validate_sbsolver_letters(letters)
        except ValueError as exc:
            st.error(str(exc))
            st.session_state.classification_results = None
        else:
            valid_letters = True
            if letters != st.session_state.puzzle_letters:
                st.session_state.puzzle_letters = letters
                set_word_list("")

    if valid_letters:
        st.link_button("Open SB Solver in your normal browser", sbsolver_link(letters))
        st.caption(
            "If automatic fetching gets stuck on a repeating security check, "
            "open this link in your usual Chrome window. Save the loaded puzzle "
            "as HTML, then upload it under Import a saved SB Solver page below. "
            "You can also paste the words manually."
        )

    if st.button(
        "Fetch Words from SB Solver", key="fetch_sbsolver", disabled=not valid_letters
    ):
        st.session_state.classification_results = None
        try:
            with st.spinner("Waiting for the SB Solver word list in Chrome..."):
                imported_words = fetch_words_sbsolver(letters)
        except Exception as exc:
            st.error(f"Could not fetch words from SB Solver: {exc}")
        else:
            set_word_list("\n".join(imported_words))
            st.success(f"Fetched {len(imported_words)} words from SB Solver.")

    with st.expander("Import a saved SB Solver page"):
        st.caption(
            "Once the words are visible in your normal Chrome window, use "
            "Save page as to save the puzzle as HTML. Upload the .html file "
            "here; the app extracts the word list without its links or formatting. "
            "If Chrome also creates a folder of page assets, you only need the HTML file."
        )
        saved_page = st.file_uploader(
            "Saved SB Solver puzzle page (.html)",
            type=["html", "htm"],
            key="sbsolver_saved_page",
        )
        if st.button(
            "Import words from saved page",
            key="import_saved_sbsolver",
            disabled=not valid_letters or saved_page is None,
        ):
            try:
                saved_words = parse_saved_sbsolver_page(saved_page.getvalue())
            except ValueError as exc:
                st.error(str(exc))
            else:
                set_word_list("\n".join(saved_words))
                st.success(f"Imported {len(saved_words)} words from the saved SB Solver page.")

    if "step1_word_list" not in st.session_state:
        st.session_state.step1_word_list = st.session_state.word_list_text

    st.text_area(
        "Paste SB Solver word list (automatically shared with Step 2)",
        height=400,
        key="step1_word_list",
        on_change=sync_word_list,
        args=("step1_word_list",),
    )

def run_classification(
    word_list_text: str,
    creator: str,
    wahoowa_override: int,
    editorial_included_text: str,
    editorial_excluded_text: str,
    progress_callback=None,
):
    words = parse_word_list(word_list_text)
    editorial_included = parse_word_list(editorial_included_text)
    editorial_excluded = parse_word_list(editorial_excluded_text)

    common, rare = classify_words(words, progress_callback=progress_callback)
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


def clear_classification_results():
    st.session_state.classification_results = None


def combine_editorial_word_lists(pasted_text: str, uploaded_file) -> str:
    uploaded_text = (
        uploaded_file.getvalue().decode("utf-8-sig")
        if uploaded_file is not None
        else ""
    )
    return "\n".join((pasted_text, uploaded_text)).strip()


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

    if "step2_word_list" not in st.session_state:
        st.session_state.step2_word_list = st.session_state.word_list_text
    word_list_text = st.text_area(
        "Word list (one word per line)",
        height=300,
        placeholder="AERATE\nARETE\nARTERY\n...",
        key="step2_word_list",
        on_change=sync_word_list,
        args=("step2_word_list",),
    )

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
        st.caption(
            "These lists override OED decisions as a final filter. Upload UTF-8 "
            "text files with one word per line, or paste below. Uploaded and "
            "pasted lists are combined. Only words in the candidate list are "
            "affected; exclusion takes precedence if a word appears in both lists."
        )
        editorial_included_file = st.file_uploader(
            "Upload editorially included words (.txt)",
            type=["txt"],
            key="editorial_included_file",
            on_change=clear_classification_results,
        )
        editorial_included_text = st.text_area(
            "Editorially included words (one per line)",
            height=150,
            placeholder="Override OED rejections: move these words into Words",
            key="editorial_included_text",
            on_change=clear_classification_results,
        )
        editorial_excluded_file = st.file_uploader(
            "Upload editorially excluded words (.txt)",
            type=["txt"],
            key="editorial_excluded_file",
            on_change=clear_classification_results,
        )
        editorial_excluded_text = st.text_area(
            "Editorially excluded words (one per line)",
            height=150,
            placeholder="Override OED approvals: move these words into Removed Words",
            key="editorial_excluded_text",
            on_change=clear_classification_results,
        )

        editorial_uploads_valid = True
        try:
            editorial_included_text = combine_editorial_word_lists(
                editorial_included_text, editorial_included_file
            )
            editorial_excluded_text = combine_editorial_word_lists(
                editorial_excluded_text, editorial_excluded_file
            )
        except UnicodeDecodeError:
            st.error(
                "Could not read an editorial word list. Save both lists as "
                "UTF-8 plain text (.txt), then upload them again."
            )
            clear_classification_results()
            editorial_uploads_valid = False

    if not word_list_text.strip():
        return

    words = parse_word_list(word_list_text)
    st.write(f"Loaded {len(words)} words for classification.")

    if st.button(
        "Classify Words", key="classify_words", disabled=not editorial_uploads_valid
    ):
        clear_classification_results()
        progress = st.progress(0.0, text=f"Processed 0 of {len(words)} words.")

        def report_progress(done: int, total: int, word: str):
            message = f"Processed {done} of {total} words."
            if word:
                message += f" Current word: {word}."
            progress.progress(done / total if total else 0.0, text=message)

        try:
            st.session_state.classification_results = run_classification(
                word_list_text,
                creator,
                wahoowa_override,
                editorial_included_text,
                editorial_excluded_text,
                progress_callback=report_progress,
            )
        except Exception as exc:
            st.error(f"Could not finish OED classification: {exc}")
        else:
            progress.progress(1.0, text=f"Finished processing {len(words)} words.")

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
