#!/usr/bin/env python3
"""
Generate test vectors for cross-platform validation of human-checkphrase.

This script generates 1000 test vectors using random addresses to ensure
comprehensive coverage of the wordlist. The vectors are saved to
test-vectors/checksums.json and serve as the source of truth for all
implementations (Rust, JavaScript, Dart).
"""

import hashlib
import json
import os
import random
import string
import sys
from pathlib import Path

# Constants (must match all implementations)
SALT = b'human-readable-checksum'
ITERATIONS = 40000
CHECKSUM_LEN = 5
KEY_BYTECOUNT = (CHECKSUM_LEN * 11 + 7) // 8

# Paths
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
WORDLIST_PATH = REPO_ROOT / 'final_wordlist.txt'
OUTPUT_PATH = REPO_ROOT / 'test-vectors' / 'checksums.json'


def load_wordlist() -> list[str]:
    """Load the canonical wordlist from the repo root."""
    with open(WORDLIST_PATH, 'r') as f:
        words = [line.strip() for line in f if line.strip()]
    
    if len(words) != 2048:
        raise ValueError(f"Wordlist must have exactly 2048 words, found {len(words)}")
    
    return words


def address_to_checksum(address: str, word_list: list[str]) -> list[str]:
    """Generate a checksum from an address using PBKDF2."""
    key = hashlib.pbkdf2_hmac(
        'sha256',
        address.encode('utf-8'),
        SALT,
        ITERATIONS,
        dklen=KEY_BYTECOUNT
    )
    
    key_int = int.from_bytes(key, 'big') >> (8 * KEY_BYTECOUNT) % 11
    
    indices = []
    for i in range(CHECKSUM_LEN):
        shift = (CHECKSUM_LEN - 1 - i) * 11
        index = (key_int >> shift) & 0x7FF
        indices.append(index)
    
    return [word_list[i] for i in indices]


def generate_random_address(prefix: str = "", length: int = 40) -> str:
    """Generate a random address-like string."""
    chars = string.ascii_letters + string.digits
    random_part = ''.join(random.choices(chars, k=length - len(prefix)))
    return prefix + random_part


def generate_test_vectors(word_list: list[str], count: int = 1000, ensure_full_coverage: bool = True) -> tuple[list[dict], set[str]]:
    """
    Generate test vectors ensuring comprehensive word coverage.
    
    Strategy:
    1. Include canonical examples from README (9 vectors)
    2. Generate random addresses until we've seen all 2048 words
    3. Continue until we reach the target count
    
    If ensure_full_coverage is True, will generate extra vectors beyond count
    to ensure all words are covered at least once.
    """
    vectors = []
    words_seen = set()
    all_words = set(word_list)
    
    # Canonical examples from README (these must always be included)
    canonical_addresses = [
        ("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "Bitcoin - Satoshi's address"),
        ("1A1zP1eP5QGefi2DMPTfTL5SLmv7DixfNa", "Bitcoin - poisoned variant"),
        ("0x742d35Cc6634C0532925a3b844Bc9e7595f5bE21", "Ethereum"),
        ("5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY", "Polkadot"),
        ("cosmos1hsk6jryyqjfhp5dhc55tc9jtckygx0eph6dd02", "Cosmos"),
        ("bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq", "Bitcoin bech32"),
        ("qzk7h3xH4Fmv2RqKpN8sT5jW9cY6gB1dL3mX0vQwEaUoZrJtS", "Quantus 1"),
        ("qzkABCDEF123456789abcdefGHIJKLMNOPQRSTUVWXYZ000001", "Quantus 2"),
        ("qzkXyZ987654321FeDcBaAbCdEfGhIjKlMnOpQrStUvWxYz99", "Quantus 3"),
    ]
    
    # Add canonical examples first
    for address, description in canonical_addresses:
        checksum = address_to_checksum(address, word_list)
        vectors.append({
            "address": address,
            "description": description,
            "expected": checksum
        })
        words_seen.update(checksum)
    
    # Address prefixes to simulate different chains
    prefixes = [
        "0x",           # Ethereum-style
        "1",            # Bitcoin legacy
        "3",            # Bitcoin P2SH
        "bc1q",         # Bitcoin bech32
        "cosmos1",      # Cosmos
        "osmo1",        # Osmosis
        "5",            # Polkadot
        "qzk",          # Quantus
        "",             # Generic
    ]
    
    # Use a fixed seed for reproducibility
    random.seed(42)
    
    vector_num = len(vectors)
    attempts = 0
    max_attempts = count * 1000  # Safety limit (increased for full coverage)
    
    while attempts < max_attempts:
        attempts += 1
        
        # Pick a random prefix
        prefix = random.choice(prefixes)
        length = random.randint(30, 64)
        address = generate_random_address(prefix, length)
        
        checksum = address_to_checksum(address, word_list)
        
        # Track which words we've seen
        new_words = set(checksum) - words_seen
        
        # Determine if we should add this vector
        need_more_vectors = len(vectors) < count
        need_more_coverage = ensure_full_coverage and words_seen != all_words
        has_new_words = len(new_words) > 0
        
        # Add if we need more vectors, or if this gives us new word coverage
        if need_more_vectors or (need_more_coverage and has_new_words):
            vector_num += 1
            vectors.append({
                "address": address,
                "description": f"Generated test vector #{vector_num}",
                "expected": checksum
            })
            words_seen.update(checksum)
        
        # Stop if we've hit count AND have full coverage (or don't need it)
        have_enough_vectors = len(vectors) >= count
        have_full_coverage = words_seen == all_words
        if have_enough_vectors and (have_full_coverage or not ensure_full_coverage):
            break
    
    return vectors, words_seen


def main():
    print("Loading canonical wordlist...")
    word_list = load_wordlist()
    print(f"Loaded {len(word_list)} words")
    
    print("\nGenerating test vectors...")
    vectors, words_seen = generate_test_vectors(word_list, count=1000)
    
    # Check word coverage
    all_words = set(word_list)
    missing_words = all_words - words_seen
    coverage = len(words_seen) / len(all_words) * 100
    
    print(f"\nGenerated {len(vectors)} test vectors")
    print(f"Word coverage: {len(words_seen)}/{len(all_words)} ({coverage:.1f}%)")
    
    if missing_words:
        print(f"Missing {len(missing_words)} words: {sorted(missing_words)[:20]}...")
    else:
        print("Full word coverage achieved!")
    
    # Create output structure
    output = {
        "version": "1.0",
        "description": "Cross-platform test vectors for human-checkphrase",
        "generated_by": "scripts/generate_test_vectors.py",
        "constants": {
            "salt": SALT.decode('utf-8'),
            "iterations": ITERATIONS,
            "checksumLength": CHECKSUM_LEN
        },
        "statistics": {
            "totalVectors": len(vectors),
            "wordsCovered": len(words_seen),
            "totalWords": len(all_words),
            "coveragePercent": round(coverage, 2)
        },
        "testCases": vectors
    }
    
    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Write output
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nSaved test vectors to {OUTPUT_PATH}")
    
    return 0 if not missing_words else 1


if __name__ == "__main__":
    sys.exit(main())
