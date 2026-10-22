# hoos_spelling_automation
A tool for the UVA Cavalier Daily's Puzzle Desk to automate the development of Hoo's Spelling puzzles.

For the Render hosting pilot, follow [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md).
Use the root Dockerfile to install the Linux browser; hosted source access is
still being verified.

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
3. In **Step 1: Import SB Solver**, enter the six actual puzzle letters plus your chosen seventh placeholder. Capitalize the actual center letter and leave the others lowercase. Click **Open puzzle in SB Solver**, wait until the word table loads in your normal browser, then use **Save page as** to save the page as HTML. Upload the `.html` file directly in Step 1 and click **Import words**. If the browser saves an accompanying assets folder, upload only the HTML file. Review the imported words shown below; import another saved page to replace them.
4. Review the imported list. To delete words, select them in **Words to remove** and click **Remove selected words**. Placeholder-containing words are kept unless you remove them. The updated list carries into **Step 2: OED Classification**, together with the puzzle title and SB Solver link. Removing words clears earlier classification results. Reimport the page to restore the original list. Candidate words come from the HTML import; there is no automatic-fetch or candidate-paste control.
5. In **Optional: Editorial word filters**, enter two Google Sheets links: one for included words and one for excluded words. Put one word per row in column A; an optional `Word` or `Words` header is supported. Use **Share → General access → Anyone with the link → Viewer**, or publish the sheet to the web. Copy the link while the desired tab is selected; if no tab ID is present, the first tab is read. Click **Load / refresh editorial lists** and confirm the counts before classifying. Either link may be blank. After editing words in Google Sheets, click Load / refresh again. These lists override OED decisions only for existing candidates, and exclusion wins on conflicts. Loading failures block classification until corrected or the link is cleared.
6. Click **Classify Words**. A progress bar shows the number of words processed and the current word, then use **Copy formatted output** to paste the finished document into Google Docs or Word in 12-point Times New Roman with clickable links. HTML and Word downloads remain available. Complete the workflow in the active session; jobs and drafts are not saved across refreshes or restarts.

## Notes

* Requires Google Chrome

* SB Solver remains the source of candidate words. OED classification uses the first search result and the existing editorial criteria, including at least three usage bars. The seventh SB Solver letter is a variable placeholder, not an additional puzzle letter; the app does not automatically remove placeholder-containing words.

* Cloudflare does not support Selenium-controlled browsers for solving production challenges. A repeating checkbox may require normal-browser access; automatic retries are not guaranteed to resolve it. See [Cloudflare's supported browser environments](https://developers.cloudflare.com/cloudflare-challenges/reference/supported-browsers/).

## Verification

The hosted app offers saved SB Solver HTML import and OED classification.
The automatic verifier has been removed from the app because SB Solver blocks
its hosted requests.

Run the offline regression checks from the repository directory:

```bash
python -m unittest discover -s tests -v
```

These check saved-page imports, import replacement and puzzle-change invalidation, editorial overrides,
progress, and the existing OED criteria using sample HTML and mocked browser
responses. They do not make live requests to either site.
