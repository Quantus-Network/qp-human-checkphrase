"""Prototype/demo script: print checkphrases for a couple of test addresses.

The actual scheme lives in checkphrase.py; this file just exercises it.
"""

from pathlib import Path

from checkphrase import address_to_checksum

WORD_LIST_FILE = Path(__file__).parent.parent / 'final_wordlist.txt'


def load_word_list():
    with open(WORD_LIST_FILE, 'r') as f:
        words = [line.strip() for line in f if line.strip()]
    if len(words) != 2048:
        raise ValueError(f"Expected 2048 words, found {len(words)}")
    print(f"Loaded {len(words)} words from {WORD_LIST_FILE}")
    return words


def main():
    word_list = load_word_list()

    # Test addresses
    test_addresses = [
        "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",  # Legit
        "1A1zP1eP5QGefi2DMPTfTL5SLmv7DixfNa"   # Poisoned
    ]
    for addr in test_addresses:
        words = address_to_checksum(addr, word_list)
        print(f"Address: {addr}")
        print(f"Checkphrase: {'-'.join(words)}")


if __name__ == "__main__":
    main()
