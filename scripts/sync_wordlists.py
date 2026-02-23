#!/usr/bin/env python3
"""
Sync wordlist files across all implementations.

This script takes the canonical final_wordlist.txt from the repo root and:
1. Copies it to dart/assets/final_wordlist.txt
2. Converts it to JSON array and writes to js/src/wordlist.json

Usage:
    python scripts/sync_wordlists.py          # Sync files
    python scripts/sync_wordlists.py --check  # Check if files are in sync (for CI)
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

# Paths relative to repo root
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent

CANONICAL_PATH = REPO_ROOT / 'final_wordlist.txt'
DART_PATH = REPO_ROOT / 'dart' / 'assets' / 'final_wordlist.txt'
JS_PATH = REPO_ROOT / 'js' / 'src' / 'wordlist.json'

EXPECTED_WORD_COUNT = 2048


def file_hash(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_canonical_wordlist() -> list[str]:
    """Load the canonical wordlist and validate it."""
    if not CANONICAL_PATH.exists():
        raise FileNotFoundError(f"Canonical wordlist not found: {CANONICAL_PATH}")
    
    with open(CANONICAL_PATH, 'r') as f:
        words = [line.strip() for line in f if line.strip()]
    
    if len(words) != EXPECTED_WORD_COUNT:
        raise ValueError(
            f"Canonical wordlist must have exactly {EXPECTED_WORD_COUNT} words, "
            f"found {len(words)}"
        )
    
    return words


def sync_dart(words: list[str], check_only: bool = False) -> bool:
    """Sync the Dart wordlist file."""
    # Dart uses the same plain text format
    expected_content = '\n'.join(words) + '\n'
    
    if DART_PATH.exists():
        current_content = DART_PATH.read_text()
        if current_content == expected_content:
            print(f"  [OK] {DART_PATH.relative_to(REPO_ROOT)}")
            return True
        else:
            print(f"  [DIFF] {DART_PATH.relative_to(REPO_ROOT)}")
            if check_only:
                return False
    else:
        print(f"  [MISSING] {DART_PATH.relative_to(REPO_ROOT)}")
        if check_only:
            return False
    
    # Write the file
    DART_PATH.parent.mkdir(parents=True, exist_ok=True)
    DART_PATH.write_text(expected_content)
    print(f"  [SYNCED] {DART_PATH.relative_to(REPO_ROOT)}")
    return True


def sync_js(words: list[str], check_only: bool = False) -> bool:
    """Sync the JavaScript wordlist file (JSON format)."""
    # JavaScript uses JSON array format
    expected_content = json.dumps(words, indent=2) + '\n'
    
    if JS_PATH.exists():
        current_content = JS_PATH.read_text()
        try:
            current_words = json.loads(current_content)
            if current_words == words:
                print(f"  [OK] {JS_PATH.relative_to(REPO_ROOT)}")
                return True
            else:
                # Show what's different
                current_set = set(current_words)
                expected_set = set(words)
                only_in_current = current_set - expected_set
                only_in_expected = expected_set - current_set
                
                print(f"  [DIFF] {JS_PATH.relative_to(REPO_ROOT)}")
                if only_in_current:
                    print(f"         Words only in JS (will be removed): {len(only_in_current)}")
                if only_in_expected:
                    print(f"         Words only in canonical (will be added): {len(only_in_expected)}")
                
                if check_only:
                    return False
        except json.JSONDecodeError:
            print(f"  [INVALID JSON] {JS_PATH.relative_to(REPO_ROOT)}")
            if check_only:
                return False
    else:
        print(f"  [MISSING] {JS_PATH.relative_to(REPO_ROOT)}")
        if check_only:
            return False
    
    # Write the file
    JS_PATH.parent.mkdir(parents=True, exist_ok=True)
    JS_PATH.write_text(expected_content)
    print(f"  [SYNCED] {JS_PATH.relative_to(REPO_ROOT)}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Sync wordlist files across all implementations'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check if files are in sync without modifying them (for CI)'
    )
    args = parser.parse_args()
    
    print("Wordlist Sync")
    print("=" * 50)
    
    # Load canonical wordlist
    print(f"\nCanonical: {CANONICAL_PATH.relative_to(REPO_ROOT)}")
    try:
        words = load_canonical_wordlist()
        canonical_hash = file_hash(CANONICAL_PATH)
        print(f"  Words: {len(words)}")
        print(f"  SHA-256: {canonical_hash[:16]}...")
    except (FileNotFoundError, ValueError) as e:
        print(f"  ERROR: {e}")
        return 1
    
    # Sync each target
    print(f"\nTargets (mode: {'check' if args.check else 'sync'}):")
    
    results = []
    results.append(sync_dart(words, check_only=args.check))
    results.append(sync_js(words, check_only=args.check))
    
    # Summary
    print("\n" + "=" * 50)
    if all(results):
        print("All wordlists are in sync!")
        return 0
    else:
        if args.check:
            print("ERROR: Wordlists are out of sync!")
            print("Run 'python scripts/sync_wordlists.py' to fix.")
            return 1
        else:
            print("Wordlists have been synchronized.")
            return 0


if __name__ == "__main__":
    sys.exit(main())
