from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

BASE_URL = "https://www.sbsolver.com/s/"


def sbsolver_link(letters: str) -> str:
    return f"{BASE_URL}{letters}"


def fetch_words_sbsolver(letters: str):
    url = sbsolver_link(letters)

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)

    try:
        driver.get(url)
        driver.implicitly_wait(5)

        word_elements = driver.find_elements(By.CSS_SELECTOR, "table.bee-set td.bee-hover a")
        words = [el.text.strip().upper() for el in word_elements if el.text.strip()]
        return words

    finally:
        driver.quit()
