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

venv\Scripts\activate      # Windows

pip install -r requirements.txt
```

## How to use (do this everytime you want to run the program)

1. First, start your venv with
```bash
source my_venv/bin/activate   # Mac/Linux

OR 

venv\Scripts\activate      # Windows
```
You should have (my_venv) at the beginning of the command line. 

2. Run the app with `streamlit run app.py`
3. In **Step 1**, enter the seven puzzle letters and fetch words from SB Solver
4. Switch to **Step 2** — the word list, puzzle title, and SB Solver link carry over automatically
5. Optionally paste editorially included/excluded word lists, then classify
6. Download results as HTML or Word document 

## Notes

* Requires Google Chrome

## Example input

See `words.txt` for a sample file.
