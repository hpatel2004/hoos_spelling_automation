# hoos_spelling_automation
A tool for the UVA Cavalier Daily's Puzzle Desk to automate the development of Hoo's Spelling puzzles.

## Setup (one time)

1. Make sure you have Python installed (3.10+ recommended)

2. Clone or download this repo by running `git clone https://github.com/hpatel2004/hoos_spelling_automation.git`, then run:

```bash
./one_time_setup
```

This creates a virtual environment, installs dependencies, and prints next steps.

To set up manually instead:

```bash
python3 -m venv my_venv # all devices

source my_venv/bin/activate   # Mac/Linux

OR 

my_venv\Scripts\activate      # Windows

pip install -r requirements.txt
```

## How to use (do this everytime you want to run the program)

1. First, start your venv with
```bash
source my_venv/bin/activate   # Mac/Linux

OR 

my_venv\Scripts\activate      # Windows
```
You should have (my_venv) at the beginning of the command line. 

2. Run the app with `streamlit run app.py`
3. In **Step 1**, enter the six actual puzzle letters plus your chosen seventh placeholder for SB Solver. Capitalize the actual center letter and leave the others lowercase, then fetch words.
   If the security checkbox keeps looping, use **Open SB Solver in your normal browser** and complete verification in your usual Chrome window. Once the word list is visible, use **Save page as** and choose an HTML format. In Step 1, expand **Import a saved SB Solver page**, upload the `.html` file, and click **Import words from saved page**. The app extracts plain words from the site's word table; no manual hyperlink or formatting cleanup is needed. If Chrome creates an accompanying asset folder, upload only the HTML file. You can still paste words manually, one per line.
4. Switch to **Step 2** — the word list, puzzle title, and SB Solver link carry over automatically
5. In **Optional: Editorial word filters**, optionally upload included and excluded word lists as UTF-8 `.txt` files (one word per line), or paste them. These override OED decisions after classification. Only candidate words are affected, and exclusion wins if a word appears in both lists. Changing a filter clears the previous results; click **Classify Words** to apply the updated lists.
6. Click **Classify Words**. A progress bar shows the number of words processed and the current word, then download results as HTML or a Word document.

## Notes

* Requires Google Chrome

* SB Solver remains the source of candidate words. OED classification uses the first search result and the existing editorial criteria, including at least three usage bars. The seventh SB Solver letter is a variable placeholder, not an additional puzzle letter; the app does not automatically remove placeholder-containing words.

* Cloudflare does not support Selenium-controlled browsers for solving production challenges. A repeating checkbox may require normal-browser access; automatic retries are not guaranteed to resolve it. See [Cloudflare's supported browser environments](https://developers.cloudflare.com/cloudflare-challenges/reference/supported-browsers/).

## Verification

Run the offline regression checks from the repository directory:

```bash
python -m unittest discover -s tests -v
```

These check saved-page imports, word-list synchronization, editorial overrides, progress, and the existing OED criteria using sample HTML and mocked browser responses. They do not make live requests to either site.
