#!/usr/bin/env python3
"""
Generate test vectors for cross-platform validation of human-checkphrase.

The vectors are saved to test-vectors/checksums.json and serve as the source
of truth for all implementations (Rust, JavaScript, Dart). Each test case may
carry optional "wordCount" and "context" fields; implementations must default
to wordCount=5 and no context when the fields are absent.

Requires argon2-cffi:  pip install argon2-cffi
"""

import json
import random
import string
import sys
from pathlib import Path

from checkphrase import (
    DEFAULT_WORD_COUNT,
    MEMORY_KIB,
    PARALLELISM,
    TIME_COST,
    VERSION,
    address_to_checksum,
)

# Paths
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
WORDLIST_PATH = REPO_ROOT / 'final_wordlist.txt'
OUTPUT_PATH = REPO_ROOT / 'test-vectors' / 'checksums.json'

RANDOM_VECTOR_COUNT = 128


def load_wordlist() -> list[str]:
    """Load the canonical wordlist from the repo root."""
    with open(WORDLIST_PATH, 'r') as f:
        words = [line.strip() for line in f if line.strip()]

    if len(words) != 2048:
        raise ValueError(f"Wordlist must have exactly 2048 words, found {len(words)}")

    return words


def generate_random_address(prefix: str = "", length: int = 40) -> str:
    """Generate a random address-like string."""
    chars = string.ascii_letters + string.digits
    random_part = ''.join(random.choices(chars, k=length - len(prefix)))
    return prefix + random_part


def make_case(word_list, address, description, word_count=None, context=None):
    case = {
        "address": address,
        "description": description,
        "expected": address_to_checksum(
            address,
            word_list,
            word_count=word_count or DEFAULT_WORD_COUNT,
            context=context,
        ),
    }
    if word_count is not None:
        case["wordCount"] = word_count
    if context is not None:
        case["context"] = context
    return case


def generate_test_vectors(word_list: list[str]) -> list[dict]:
    vectors = []

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
    for address, description in canonical_addresses:
        vectors.append(make_case(word_list, address, description))

    # Normalization: these must match the canonical Ethereum vector above.
    eth = "0x742d35Cc6634C0532925a3b844Bc9e7595f5bE21"
    vectors.append(make_case(
        word_list, eth.lower(),
        "Normalization - Ethereum all-lowercase (same phrase as EIP-55 form)"))
    vectors.append(make_case(
        word_list, "0X" + eth[2:].upper(),
        "Normalization - Ethereum 0X-uppercase (same phrase as EIP-55 form)"))
    vectors.append(make_case(
        word_list, f"  {eth}\n",
        "Normalization - surrounding whitespace is stripped"))
    # Base58 is case-sensitive: no lowercasing must be applied.
    vectors.append(make_case(
        word_list, "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa".lower(),
        "Normalization - lowercased base58 is a DIFFERENT address/phrase"))

    # Non-default word counts.
    for wc in (3, 4, 6, 8, 11):
        vectors.append(make_case(
            word_list, "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            f"Word count {wc} - Satoshi's address", word_count=wc))

    # Domain-separation context (e.g. a chain id).
    vectors.append(make_case(
        word_list, "qzk7h3xH4Fmv2RqKpN8sT5jW9cY6gB1dL3mX0vQwEaUoZrJtS",
        "Context 'quantus' - salt becomes 'human-checkphrase-v2|quantus'",
        context="quantus"))
    vectors.append(make_case(
        word_list, "0x742d35Cc6634C0532925a3b844Bc9e7595f5bE21",
        "Context 'eip155:1' - Ethereum mainnet domain separation",
        context="eip155:1"))
    vectors.append(make_case(
        word_list, "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
        "Context 'bitcoin' with word count 8", word_count=8, context="bitcoin"))

    # Random addresses across chain-style prefixes.
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

    for i in range(RANDOM_VECTOR_COUNT):
        prefix = random.choice(prefixes)
        length = random.randint(30, 64)
        address = generate_random_address(prefix, length)
        vectors.append(make_case(
            word_list, address, f"Generated test vector #{i + 1}"))

    return vectors


def main():
    print("Loading canonical wordlist...")
    word_list = load_wordlist()
    print(f"Loaded {len(word_list)} words")

    print("\nGenerating test vectors (Argon2id is intentionally slow)...")
    vectors = generate_test_vectors(word_list)

    words_seen = set()
    for case in vectors:
        words_seen.update(case["expected"])
    coverage = len(words_seen) / len(word_list) * 100

    print(f"\nGenerated {len(vectors)} test vectors")
    print(f"Word coverage: {len(words_seen)}/{len(word_list)} ({coverage:.1f}%)")

    output = {
        "version": "2.0",
        "description": "Cross-platform test vectors for human-checkphrase",
        "generated_by": "scripts/generate_test_vectors.py",
        "constants": {
            "kdf": "argon2id",
            "argon2Version": 19,
            "memoryKiB": MEMORY_KIB,
            "timeCost": TIME_COST,
            "parallelism": PARALLELISM,
            "salt": VERSION,
            "defaultWordCount": DEFAULT_WORD_COUNT,
        },
        "statistics": {
            "totalVectors": len(vectors),
            "wordsCovered": len(words_seen),
            "totalWords": len(word_list),
            "coveragePercent": round(coverage, 2),
        },
        "testCases": vectors,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved test vectors to {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
