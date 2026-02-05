import requests
import hashlib
import hmac
import os

# Constants
WORD_LIST_FILE = 'final_wordlist.txt'
BIP39_URL = "https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/english.txt"
ITERATIONS = 40000
SALT = b'human-readable-checksum'
CHECKSUM_LEN = 5
KEY_BYTECOUNT = (CHECKSUM_LEN * 11 + 7) // 8


# Fetch or load BIP-39 list
def load_bip39_list(local_file=WORD_LIST_FILE, url=BIP39_URL):
    """Load the BIP-39 list from local file if it exists, otherwise fetch it."""
    # Check if local file exists and has content
    if os.path.exists(local_file) and os.path.getsize(local_file) > 0:
        with open(local_file, 'r') as f:
            words = [line.strip() for line in f]
        if len(words) == 2048:  # Verify it’s the full list
            print(f"Loaded {len(words)} words from {local_file}")
            return words
        else:
            print(f"Local file {local_file} is incomplete, re-downloading...")

    # Fetch from URL if local file is missing or invalid
    response = requests.get(url)
    if response.status_code == 200:
        words = response.text.strip().split('\n')
        if len(words) == 2048:
            save_word_list(words, local_file)  # Save for next time
            return words
    raise Exception("Failed to fetch or validate BIP-39 list")

# PBKDF2-based checksum
def address_to_checksum(address, word_list):
    """Generate a four-word checksum from an address using PBKDF2."""
    key = hashlib.pbkdf2_hmac(
        'sha256',
        address.encode('utf-8'),
        SALT,
        ITERATIONS,
        dklen=KEY_BYTECOUNT
    )
    print("key {}".format(key.hex()))
    key_int = int.from_bytes(key, 'big') >> (8 * KEY_BYTECOUNT) % 11
    print("key_int {}".format(key_int))
    indices = []
    for i in range(CHECKSUM_LEN):
        shift = (CHECKSUM_LEN - 1 - i) * 11
        index = (key_int >> shift) & 0x7FF
        indices.append(index)

    print("indices {}".format(indices))
    return [word_list[i] for i in indices]

def save_word_list(word_list, output_file=WORD_LIST_FILE):
    """Save the word list to a file."""
    with open(output_file, 'w') as f:
        for word in word_list:
            f.write(word + '\n')
    print(f"Saved {len(word_list)} words to {output_file}")

def main():
    # Load or fetch BIP-39 list
    bip39_list = load_bip39_list()
    print(f"Total combos: {len(bip39_list)**CHECKSUM_LEN:,}")
    print(f"Sample: {bip39_list[:CHECKSUM_LEN]} ... {bip39_list[-CHECKSUM_LEN:]}")

    # Test addresses
    test_addresses = [
        "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",  # Legit
        "1A1zP1eP5QGefi2DMPTfTL5SLmv7DixfNa"   # Poisoned
    ]
    for addr in test_addresses:
        four_words = address_to_checksum(addr, bip39_list)
        print(f"Address: {addr}")
        print(f"Checksum: {'-'.join(four_words)}")

if __name__ == "__main__":
    main()