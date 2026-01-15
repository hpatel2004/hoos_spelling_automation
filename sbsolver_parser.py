import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import tempfile
import os

BASE_URL = "https://www.sbsolver.com/s/"

# ------------------------------
# SB Solver Selenium Scraper
# ------------------------------
def fetch_words_sbsolver(letters: str):
    url = BASE_URL + letters

    options = Options()
    options.add_argument("--headless=new")  # headless Chrome
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get(url)
        # Wait a few seconds for JS to render
        driver.implicitly_wait(5)

        # Grab words from the table
        word_elements = driver.find_elements(By.CSS_SELECTOR, "table.bee-set td.bee-hover a")
        words = [el.text.strip().upper() for el in word_elements if el.text.strip()]
        return words

    finally:
        driver.quit()


# ------------------------------
# Streamlit UI
# ------------------------------
st.set_page_config(page_title="Hoos Spelling Puzzle - Step 1")

st.title("Hoos Spelling Puzzle Generator (Step 1)")

letters = st.text_input("Enter letters (e.g., pRincej)")

if st.button("Fetch Words") and letters:
    with st.spinner("Fetching words from SB Solver..."):
        try:
            words = fetch_words_sbsolver(letters)
            if not words:
                st.error("No words found. Make sure the letters are valid.")
            else:
                st.success(f"Fetched {len(words)} words.")
                # Display words
                st.text("\n".join(words))

                # Create downloadable TXT
                txt_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
                txt_file.write("\n".join(words).encode("utf-8"))
                txt_file.close()
                st.download_button("Download Word List (TXT)", data=open(txt_file.name, "rb"), file_name="words.txt")
                # Clean up temp file on app exit
                st.experimental_set_query_params(tempfile=txt_file.name)

        except Exception as e:
            st.error(f"Error fetching words: {e}")
