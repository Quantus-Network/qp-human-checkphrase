import { argon2id } from "hash-wasm";
import wordlist from "./wordlist.json";

// Scheme version string, also used as the Argon2 salt (optionally extended
// with a domain-separation context: "human-checkphrase-v2|<context>").
const VERSION = "human-checkphrase-v2";

// Argon2id parameters (RFC 9106), must match all other implementations.
const MEMORY_KIB = 64 * 1024;
const TIME_COST = 3;
const PARALLELISM = 1;

const DEFAULT_WORD_COUNT = 5;
// Argon2 output must be at least 4 bytes; 3 words -> 5 key bytes.
const MIN_WORD_COUNT = 3;
// 11 words = 121 bits; keeps parity with the Rust implementation's u128.
const MAX_WORD_COUNT = 11;

export interface ChecksumOptions {
  /** Number of words in the phrase (3-11). Defaults to 5. */
  wordCount?: number;
  /**
   * Optional domain-separation context (e.g. a chain id such as "eip155:1").
   * Two wallets must use the same context to see the same phrase.
   */
  context?: string;
}

const loadWordList = (): string[] => {
  return wordlist;
};

/**
 * Canonicalize an address string before hashing.
 *
 * Surrounding whitespace is stripped. 0x-prefixed hexadecimal addresses are
 * lowercased so that EIP-55 checksum casing does not change the checkphrase.
 * All other encodings (base58, bech32, SS58, ...) are case-sensitive and are
 * passed through unchanged; callers must supply them in canonical form.
 */
const normalizeAddress = (address: string): string => {
  const trimmed = address.trim();
  if (/^0[xX][0-9a-fA-F]+$/.test(trimmed)) {
    return trimmed.toLowerCase();
  }
  return trimmed;
};

const addressToChecksum = async (
  address: string,
  wordList: string[],
  options: ChecksumOptions = {},
): Promise<string[]> => {
  const wordCount = options.wordCount ?? DEFAULT_WORD_COUNT;
  if (wordCount < MIN_WORD_COUNT || wordCount > MAX_WORD_COUNT) {
    throw new RangeError(
      `wordCount must be between ${MIN_WORD_COUNT} and ${MAX_WORD_COUNT}, got ${wordCount}`,
    );
  }

  const keyByteCount = Math.ceil((wordCount * 11) / 8);
  const salt = options.context ? `${VERSION}|${options.context}` : VERSION;

  // Argon2id: memory-hard KDF so that GPU/ASIC farms cannot grind
  // checkphrase collisions much faster than commodity hardware.
  const key = await argon2id({
    password: normalizeAddress(address),
    salt,
    iterations: TIME_COST,
    memorySize: MEMORY_KIB,
    parallelism: PARALLELISM,
    hashLength: keyByteCount,
    outputType: "binary",
  });

  // Convert key bytes to a big integer (using BigInt for arbitrary precision)
  let keyInt = 0n;
  for (let i = 0; i < keyByteCount; i++) {
    keyInt = (keyInt << 8n) | BigInt(key[i]);
  }

  // Take only the first wordCount * 11 bits
  keyInt >>= BigInt((8 * keyByteCount) % 11);

  // Split into 11-bit indices
  const indices: number[] = [];
  for (let i = 0; i < wordCount; i++) {
    const shift = BigInt((wordCount - 1 - i) * 11);
    const index = Number((keyInt >> shift) & 0x7ffn);
    indices.push(index);
  }

  // Map to words
  return indices.map((i) => wordList[i]);
};

export { loadWordList, normalizeAddress, addressToChecksum, VERSION };
