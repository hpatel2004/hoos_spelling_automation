# hoos_spelling_automation
A tool for the UVA Cavalier Daily's Puzzle Desk to automate the development of Hoo's Spelling puzzles.

## Setup (one time)

1. Make sure you have Python installed (3.10+ recommended)

2. Clone or download this repo by running `git clone https://github.com/hpatel2004/hoos_spelling_automation.git`, then run:

```bash
python3 -m venv my_venv # all devices

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

2. To generate the list of words from sbsolver, run `streamlit run sbsolver_parser.py`
3. Download the generated list as a .txt
4. To classify the words by the OED, run `streamlit run oed_parser.py`
5. Upload your .txt of words
6. Download results as HTML or Word document. 

## Notes

* Requires Google Chrome

## Example input

See `words.txt` for a sample file.
