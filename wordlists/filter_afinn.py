#!/usr/bin/env python3
"""
Filter AFINN wordlist for positive words only.

AFINN format is tab-separated: word<TAB>score
Scores range from -5 (very negative) to +5 (very positive).

Usage:
    python filter_afinn.py \
        --input afinn.txt \
        --output positive_candidates.txt \
        --min-score 1 \
        --min-length 3 \
        --max-length 8
"""

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description='Filter AFINN wordlist for positive words only.'
    )
    parser.add_argument(
        '--input', '-i',
        type=Path,
        required=True,
        help='Path to AFINN wordlist file (tab-separated: word<TAB>score)'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        required=True,
        help='Path to write filtered positive words (one per line)'
    )
    parser.add_argument(
        '--min-score', '-s',
        type=int,
        default=1,
        help='Minimum score to include (default: 1, meaning any positive)'
    )
    parser.add_argument(
        '--min-length',
        type=int,
        default=3,
        help='Minimum word length (default: 3)'
    )
    parser.add_argument(
        '--max-length',
        type=int,
        default=8,
        help='Maximum word length (default: 8)'
    )
    
    args = parser.parse_args()
    
    print(f"Loading AFINN wordlist from {args.input}...")
    
    positive_words = []
    skipped_negative = 0
    skipped_hyphenated = 0
    skipped_spaces = 0
    skipped_too_short = 0
    skipped_too_long = 0
    skipped_invalid = 0
    
    with open(args.input, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            # Parse tab-separated format
            parts = line.split('\t')
            if len(parts) != 2:
                skipped_invalid += 1
                print(f"  - Skipped line {line_num}: invalid format '{line[:30]}...'")
                continue
            
            word, score_str = parts
            word = word.strip().lower()
            
            try:
                score = int(score_str)
            except ValueError:
                skipped_invalid += 1
                print(f"  - Skipped line {line_num}: invalid score '{score_str}'")
                continue
            
            # Filter: must be positive
            if score < args.min_score:
                skipped_negative += 1
                continue
            
            # Filter: no hyphens
            if '-' in word:
                skipped_hyphenated += 1
                continue
            
            # Filter: no spaces (multi-word phrases)
            if ' ' in word:
                skipped_spaces += 1
                continue
            
            # Filter: word length
            if len(word) < args.min_length:
                skipped_too_short += 1
                continue
            
            if len(word) > args.max_length:
                skipped_too_long += 1
                continue
            
            positive_words.append(word)
    
    # Remove duplicates and sort
    positive_words = sorted(set(positive_words))
    
    # Write output
    print(f"\nWriting {len(positive_words)} words to {args.output}...")
    with open(args.output, 'w', encoding='utf-8') as f:
        for word in positive_words:
            f.write(word + '\n')
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Positive words found:  {len(positive_words)}")
    print(f"  Skipped (negative):    {skipped_negative}")
    print(f"  Skipped (hyphenated):  {skipped_hyphenated}")
    print(f"  Skipped (spaces):      {skipped_spaces}")
    print(f"  Skipped (too short):   {skipped_too_short} (< {args.min_length} chars)")
    print(f"  Skipped (too long):    {skipped_too_long} (> {args.max_length} chars)")
    print(f"  Skipped (invalid):     {skipped_invalid}")
    print("=" * 60)
    print(f"\nOutput written to: {args.output}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
