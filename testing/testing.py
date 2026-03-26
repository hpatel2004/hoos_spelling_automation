import os
from bs4 import BeautifulSoup

# ------------------------
# Import your Phase 2 functions
# ------------------------
# Assume your OED classification logic is in a script called oed_parser.py
# and the main function that does classification is called classify_words(words)
# which returns: common_words_list, rare_words_list (both lists of strings)
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from oed_parser import classify_words

# ------------------------
# Helper functions
# ------------------------
def read_word_list(filename):
    """Read a newline-separated file, return a set of uppercase words."""
    with open(filename, "r") as f:
        return {line.strip().upper() for line in f if line.strip()}

# ------------------------
# User inputs
# ------------------------
letter_set = "hiKersx"
input_words_file = "hiKers_words.txt"          # Word list to classify
included_file = "hiKers_included.txt"         # Words that must be common
excluded_file = "hiKers_excluded.txt"         # Words that must NOT be common

# ------------------------
# Load input word list
# ------------------------
words_to_classify = [w.upper() for w in read_word_list(input_words_file)]

# ------------------------
# Load expected included/excluded lists
# ------------------------
included = read_word_list(included_file)
excluded = read_word_list(excluded_file)

# ------------------------
# Run Phase 2 classification
# ------------------------
common_words, rare_words = classify_words(words_to_classify)

# Normalize to sets for testing
common_words_set = {w.upper() for w in common_words}
rare_words_set   = {w.upper() for w in rare_words}

# ------------------------
# Compare results
# ------------------------
missing_in_common = included - common_words_set
extra_in_common   = excluded & common_words_set

print(f"\nPuzzle: {letter_set}")
print(f"Total words in common list: {len(common_words_set)}")
print(f"Total words in rare list: {len(rare_words_set)}\n")

if missing_in_common:
    print("❌ Included words missing from common list:", missing_in_common)
else:
    print("✅ All included words correctly in common list")

if extra_in_common:
    print("❌ Excluded words incorrectly in common list:", extra_in_common)
else:
    print("✅ No excluded words in common list")

if not missing_in_common and not extra_in_common:
    print("🎉 Phase 2 Test Passed!")
else:
    print("⚠️ Phase 2 Test Failed")
