import * as pbkdf2 from "pbkdf2";
import wordlist from "./wordlist.json";

// Constants
const SALT = "human-readable-checksum";
const ITERATIONS = 40_000;
const CHECKSUM_LEN = 5;
// Fix: Use Math.ceil to round up to the nearest integer
const KEY_BYTECOUNT = Math.ceil((CHECKSUM_LEN * 11) / 8);

const loadWordList = (): string[] => {
  return wordlist;
};

const addressToChecksum = (address: string, wordList: string[]) => {
  // PBKDF2-HMAC-SHA256 using the pbkdf2 package
  const key = pbkdf2.pbkdf2Sync(
    address,
    SALT,
    ITERATIONS,
    KEY_BYTECOUNT,
    "sha256",
  );

  // Convert key bytes to a big integer (using BigInt for arbitrary precision)
  let keyInt = 0n;
  for (let i = 0; i < KEY_BYTECOUNT && i < key.length; i++) {
    keyInt = (keyInt << 8n) | BigInt(key[i]);
  }

  // Take only the first CHECKSUM_LEN * 11 bits
  keyInt >>= BigInt((8 * KEY_BYTECOUNT) % 11);

  // Split into 11-bit indices
  const indices: number[] = [];
  for (let i = 0; i < CHECKSUM_LEN; i++) {
    const shift = BigInt((CHECKSUM_LEN - 1 - i) * 11);
    const index = Number((keyInt >> shift) & 0x7ffn);
    indices.push(index);
  }

  // Map to words
  return indices.map((i) => wordList[i]);
};

export { loadWordList, addressToChecksum };
