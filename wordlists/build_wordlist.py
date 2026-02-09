#!/usr/bin/env python3
"""
Build a wordlist by adding candidate words to an existing list,
ensuring no two words share the same 4-character prefix.

Usage:
    python build_wordlist.py \
        --existing wordlist.txt \
        --candidates candidates.txt \
        --output output.txt \
        --max-words 2048
"""

import argparse
import sys
from pathlib import Path


def load_words(filepath: Path) -> list[str]:
    """Load words from a file, one per line, stripped and lowercased."""
    words = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            word = line.strip().lower()
            if word:  # Skip empty lines
                words.append(word)
    return words


def get_prefix(word: str, length: int = 4) -> str:
    """Get the prefix of a word. If word is shorter than length, return the whole word."""
    return word[:length]


def build_prefix_map(words: list[str]) -> dict[str, str]:
    """
    Build a map of prefix -> word for a list of words.
    Returns the mapping and prints warnings for any duplicates.
    """
    prefix_map = {}
    duplicates = []
    
    for word in words:
        prefix = get_prefix(word)
        if prefix in prefix_map:
            duplicates.append((word, prefix, prefix_map[prefix]))
        else:
            prefix_map[prefix] = word
    
    return prefix_map, duplicates


def main():
    parser = argparse.ArgumentParser(
        description='Build a wordlist by adding candidates that have unique 4-char prefixes.'
    )
    parser.add_argument(
        '--existing', '-e',
        type=Path,
        required=True,
        help='Path to file with existing words (one per line)'
    )
    parser.add_argument(
        '--candidates', '-c',
        type=Path,
        required=True,
        help='Path to file with candidate words to add (one per line)'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        required=True,
        help='Path to write the resulting wordlist'
    )
    parser.add_argument(
        '--max-words', '-m',
        type=int,
        default=2048,
        help='Maximum total words in output (default: 2048)'
    )
    
    args = parser.parse_args()
    
    # Load existing words
    print(f"Loading existing words from {args.existing}...")
    existing_words = load_words(args.existing)
    existing_set = set(existing_words)
    
    # Build prefix map from existing words
    prefix_map, duplicates = build_prefix_map(existing_words)
    
    print(f"  Loaded {len(existing_words)} words with {len(prefix_map)} unique prefixes")
    
    # Warn about any duplicate prefixes in existing list
    if duplicates:
        print(f"\n  WARNING: Found {len(duplicates)} duplicate prefixes in existing list:")
        for word, prefix, conflicting in duplicates:
            print(f"    '{word}' has prefix '{prefix}' which conflicts with '{conflicting}'")
        print()
    
    # Load candidates
    print(f"\nLoading candidates from {args.candidates}...")
    candidates = load_words(args.candidates)
    print(f"  Loaded {len(candidates)} candidate words")
    
    # Process candidates
    print(f"\nProcessing candidates (max total words: {args.max_words})...\n")
    
    added_words = []
    rejected_words = []
    skipped_duplicates = []
    skipped_hyphenated = []
    
    current_total = len(existing_set)
    
    for candidate in candidates:
        # Check if we've hit the limit
        if current_total >= args.max_words:
            print(f"\n  Reached maximum of {args.max_words} words, stopping.")
            break
        
        # Skip hyphenated words
        if '-' in candidate:
            skipped_hyphenated.append(candidate)
            print(f"  - Skipped: '{candidate}' (hyphenated)")
            continue
        
        # Skip if already in existing set
        if candidate in existing_set:
            skipped_duplicates.append(candidate)
            print(f"  - Skipped: '{candidate}' (already in existing list)")
            continue
        
        prefix = get_prefix(candidate)
        
        # Check if prefix is available
        if prefix in prefix_map:
            conflicting = prefix_map[prefix]
            rejected_words.append((candidate, prefix, conflicting))
            print(f"  x Rejected: '{candidate}' (prefix '{prefix}' conflicts with '{conflicting}')")
        else:
            # Add the word
            added_words.append(candidate)
            prefix_map[prefix] = candidate
            existing_set.add(candidate)
            current_total += 1
            print(f"  + Added: '{candidate}' (prefix: '{prefix}') [{current_total}/{args.max_words}]")
    
    # Combine and sort
    final_words = sorted(existing_set)
    
    # Write output
    print(f"\nWriting {len(final_words)} words to {args.output}...")
    with open(args.output, 'w', encoding='utf-8') as f:
        for word in final_words:
            f.write(word + '\n')
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Existing words:        {len(existing_words)}")
    print(f"  Candidates processed:  {len(candidates)}")
    print(f"  Candidates added:      {len(added_words)}")
    print(f"  Candidates rejected:   {len(rejected_words)} (prefix conflict)")
    print(f"  Skipped (hyphenated):  {len(skipped_hyphenated)}")
    print(f"  Skipped (duplicate):   {len(skipped_duplicates)}")
    print(f"  Final word count:      {len(final_words)}")
    print(f"  Remaining capacity:    {args.max_words - len(final_words)}")
    print("=" * 60)
    print(f"\nOutput written to: {args.output}")
    
    # Show list of added words
    if added_words:
        print(f"\nADDED WORDS ({len(added_words)}):")
        print("-" * 40)
        for word in sorted(added_words):
            print(f"  {word}")
    
    # Return appropriate exit code
    if len(final_words) < args.max_words:
        remaining = args.max_words - len(final_words)
        print(f"\nNote: Still need {remaining} more words to reach {args.max_words}")
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
