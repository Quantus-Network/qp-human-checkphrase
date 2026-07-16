"""
Reference implementation of the human-checkphrase v2 scheme.

Scheme (must match the Rust, JavaScript and Dart implementations):

1. Normalize the address string:
   - strip leading/trailing whitespace
   - if the address is 0x-prefixed hexadecimal, lowercase it (EIP-55 casing
     must not change the checkphrase); all other encodings are case-sensitive
     and passed through unchanged
2. Derive key bytes with Argon2id (RFC 9106):
   - memory = 64 MiB, time cost = 3, parallelism = 1, version 0x13
   - salt = "human-checkphrase-v2", or "human-checkphrase-v2|<context>" when
     a domain-separation context (e.g. a chain id) is supplied
   - output length = ceil(word_count * 11 / 8) bytes
3. Interpret the key bytes as a big-endian integer, drop the
   (8 * key_len) % 11 low bits, and split the remainder into word_count
   11-bit indices into the 2048-word list.
"""

import re

from argon2.low_level import Type, hash_secret_raw

VERSION = "human-checkphrase-v2"
MEMORY_KIB = 65536  # 64 MiB
TIME_COST = 3
PARALLELISM = 1
DEFAULT_WORD_COUNT = 5
# Argon2 requires at least 4 output bytes; 3 words -> ceil(33/8) = 5 bytes.
MIN_WORD_COUNT = 3
MAX_WORD_COUNT = 11

_HEX_ADDRESS_RE = re.compile(r"0[xX][0-9a-fA-F]+\Z")


def normalize_address(address: str) -> str:
    """Canonicalize an address string before hashing."""
    stripped = address.strip()
    if _HEX_ADDRESS_RE.fullmatch(stripped):
        return stripped.lower()
    return stripped


def checkphrase_salt(context: str | None = None) -> str:
    """Versioned salt, optionally domain-separated by a chain context."""
    if context:
        return f"{VERSION}|{context}"
    return VERSION


def address_to_checksum(
    address: str,
    word_list: list[str],
    word_count: int = DEFAULT_WORD_COUNT,
    context: str | None = None,
) -> list[str]:
    """Generate a human-readable checkphrase for an address."""
    if not MIN_WORD_COUNT <= word_count <= MAX_WORD_COUNT:
        raise ValueError(
            f"word_count must be between {MIN_WORD_COUNT} and {MAX_WORD_COUNT}"
        )

    key_len = (word_count * 11 + 7) // 8
    key = hash_secret_raw(
        secret=normalize_address(address).encode("utf-8"),
        salt=checkphrase_salt(context).encode("utf-8"),
        time_cost=TIME_COST,
        memory_cost=MEMORY_KIB,
        parallelism=PARALLELISM,
        hash_len=key_len,
        type=Type.ID,
    )

    key_int = int.from_bytes(key, "big") >> (8 * key_len) % 11

    indices = []
    for i in range(word_count):
        shift = (word_count - 1 - i) * 11
        indices.append((key_int >> shift) & 0x7FF)

    return [word_list[i] for i in indices]
