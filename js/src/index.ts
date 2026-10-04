import wordlist from "./wordlist.json";

// Constants
const SALT = "human-readable-checksum";
const ITERATIONS = 40_000;
const CHECKSUM_LEN = 5;
// Fix: Use Math.ceil to round up to the nearest integer
const KEY_BYTECOUNT = Math.ceil((CHECKSUM_LEN * 11) / 8);
// Derive a full SHA-256 block, then keep the prefix. PBKDF2 defines a shorter
// key as that prefix, and some WebKit builds reject deriveBits lengths shorter
// than the hash output.
const SHA256_BITS = 256;

const textEncoder = new TextEncoder();

const loadWordList = (): string[] => {
  return wordlist;
};

const pbkdf2Sha256 = async (
  password: string,
  salt: string,
  iterations: number,
  keyBytes: number,
): Promise<Uint8Array> => {
  if (keyBytes > SHA256_BITS / 8) {
    throw new Error(
      `PBKDF2 output of ${keyBytes} bytes exceeds one SHA-256 block`,
    );
  }

  const subtle = globalThis.crypto?.subtle;
  if (!subtle) {
    throw new Error("Web Crypto is not available");
  }

  const key = await subtle.importKey(
    "raw",
    textEncoder.encode(password),
    "PBKDF2",
    false,
    ["deriveBits"],
  );

  const bits = await subtle.deriveBits(
    {
      name: "PBKDF2",
      hash: "SHA-256",
      salt: textEncoder.encode(salt),
      iterations,
    },
    key,
    SHA256_BITS,
  );

  return new Uint8Array(bits).slice(0, keyBytes);
};

const addressToChecksum = async (
  address: string,
  wordList: string[],
): Promise<string[]> => {
  const key = await pbkdf2Sha256(address, SALT, ITERATIONS, KEY_BYTECOUNT);

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
