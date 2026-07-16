# human-checkphrase

A tool to generate human-readable checksums from cryptocurrency addresses using a curated positive wordlist and Argon2id.
Designed to make address verification easier and prevent address poisoning attacks—where attackers craft lookalike addresses to trick users, this tool can be used with any existing blockchain address. Users viewing an address can also be presented with a unique, memorable phrase.

## Examples

| Address | Chain | Checkphrase |
|---------|-------|-------------|
| `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa` | Bitcoin | Cake-Stuff-Nerve-Job-Subway |
| `1A1zP1eP5QGefi2DMPTfTL5SLmv7DixfNa` | Bitcoin (poisoned) | Polar-Pet-Music-Already-Act |
| `0x742d35Cc6634C0532925a3b844Bc9e7595f5bE21` | Ethereum | Meaningful-Curve-Raccoon-Festival-Scan |
| `5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY` | Polkadot | Cricket-Rare-Significant-Above-Grateful |
| `cosmos1hsk6jryyqjfhp5dhc55tc9jtckygx0eph6dd02` | Cosmos | Dash-Health-Unfazed-Section-Ivory |
| `bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq` | Bitcoin (bech32) | History-Unbound-Fix-Add-Alter |
| `qzk7h3xH4Fmv2RqKpN8sT5jW9cY6gB1dL3mX0vQwEaUoZrJtS` | Quantus | Mimic-Advance-Satisfy-Unusual-Tell |
| `qzkABCDEF123456789abcdefGHIJKLMNOPQRSTUVWXYZ000001` | Quantus | Gap-Puppy-Cipher-Topic-Food |
| `qzkXyZ987654321FeDcBaAbCdEfGhIjKlMnOpQrStUvWxYz99` | Quantus | Cycle-Boost-Sustain-Exuberance-Course |

Notice how the first two Bitcoin addresses differ by only one character (`v` vs `x`) but produce completely different checkphrases—this is exactly what helps prevent address poisoning attacks.

## The scheme (v2)

1. **Normalize the address.** Surrounding whitespace is stripped. `0x`-prefixed
   hexadecimal addresses are lowercased so that EIP-55 checksum casing does not
   change the checkphrase (two wallets displaying the same Ethereum address with
   different casing must show the same phrase). All other encodings (base58,
   bech32, SS58, ...) are case-sensitive and passed through unchanged; callers
   must supply them in canonical form (e.g. lowercase bech32).
2. **Derive key bytes with Argon2id** (RFC 9106): 64 MiB memory, 3 passes,
   parallelism 1, version 0x13. The salt is the scheme version string
   `human-checkphrase-v2`, optionally extended with a caller-supplied
   domain-separation context: `human-checkphrase-v2|<context>` (e.g. a chain id
   such as `eip155:1`). Two wallets must use the same context—or none—to see
   the same phrase for an address. Any future change to the KDF, its
   parameters, or the wordlist bumps the version string.
3. **Map to words.** The output (`ceil(wordCount * 11 / 8)` bytes) is read as a
   big-endian integer, the low `(8 * len) % 11` bits are dropped, and the
   remaining bits are split into `wordCount` 11-bit indices into the
   2048-word list.

The word count is configurable from 3 to 11 words and defaults to **5 words
(55 bits)**. Five words are appropriate for the intended use: *verification*,
i.e. comparing the phrase of an address you already have against the phrase
you expect. If you ever use phrases as identifiers (e.g. looking up an address
by phrase), you need collision resistance against multi-target attacks—use 8+
words (88+ bits), and see the security analysis below.

## Wordlist

The wordlist (`final_wordlist.txt`) contains exactly 2048 words, designed to be:
- **Positive and friendly** - People should feel good when reading them
- **Unique** - No two words share the same 4-character prefix (for easy autocomplete)
- **Recognizable** - Common English words that are easy to read and remember

The wordlist was curated by combining and filtering several sources:

| Source | Description |
|--------|-------------|
| [BIP-39](https://github.com/bitcoin/bips/blob/master/bip-0039/english.txt) | Standard Bitcoin mnemonic wordlist (2048 words) - used as base, negative words removed |
| [AFINN](https://github.com/fnielsen/afinn) | Sentiment lexicon with words scored -5 to +5 - filtered for positive words only |
| [Bing Liu Opinion Lexicon](https://www.cs.uic.edu/~liub/FBS/sentiment-analysis.html) | Curated list of positive/negative opinion words |
| Crypto terminology | Domain-specific positive terms (stake, mint, wallet, verified, etc.) |

Build tools for maintaining the wordlist are in `wordlists/`.

### Syncing Wordlists

The canonical wordlist is `final_wordlist.txt` in the repo root. Copies exist in `js/` and `dart/` for packaging. To sync after editing the canonical file:

```bash
python3 scripts/sync_wordlists.py
```

To regenerate test vectors (requires `pip install argon2-cffi`):

```bash
python3 scripts/generate_test_vectors.py
```

## This repo contains

- **Rust**: A library crate at the root for fast, reusable checksum generation
- **JavaScript/TypeScript**: NPM package in `js/`
- **Dart**: Pub package in `dart/`
- **Python**: Reference implementation in `scripts/checkphrase.py`

### Running tests

```bash
./run_tests.sh
```

Or run individually:
- Rust: `cargo test --release -- --nocapture`
- JavaScript: `cd js && npm test`
- Dart: `cd dart && dart test`

Tests validate against shared test vectors in `test-vectors/checksums.json`—including
normalization, non-default word counts, and domain-separation contexts—to ensure all
implementations produce identical results.

## Security Analysis

Each word carries 11 bits (2048 choices), so the default 5-word phrase has
2^55 ≈ 36 quadrillion possible values.

### Threat model: verification vs. identification

The checkphrase is a *verification* aid: the user already holds an address and
compares its phrase against the one they expect. An attacker (e.g. address
poisoning) must therefore generate an address whose phrase matches one
*specific* 55-bit target—a second-preimage attack requiring ~2^55 KDF
evaluations in expectation.

The phrase is **not** an identifier. If phrases are used to *look up*
addresses, an attacker profits from colliding with *any* of N valuable
addresses at once, which cuts the work to 2^55 / N; with a million targets
that is only ~2^35 evaluations. Reverse lookup also turns a collision from a
visible mismatch into a coin-flip for the user. If you need lookup, use 8+
words and a registry that enforces phrase uniqueness.

### Why Argon2id instead of PBKDF2

Version 1 of this scheme used PBKDF2-HMAC-SHA256 (40,000 iterations). PBKDF2
imposes only compute cost, and SHA-256 is the most hardware-accelerated
function in existence: a single consumer GPU computes ~20 GH/s of SHA-256,
i.e. ~250,000 PBKDF2-40k guesses per second—about 3,500x faster than the
~14 ms a defender pays per phrase. Bitcoin-mining ASICs widen that gap by
several more orders of magnitude.

Argon2id is *memory-hard*: every evaluation must fill and randomly access
64 MiB. Attacker throughput is then bounded by memory size and bandwidth, not
core count—a 24 GB GPU fits only ~375 concurrent instances and its bandwidth
supports on the order of 10^3 guesses/second, within ~100x of a defender's
laptop core instead of the ~10^5-10^8x gap for SHA-256-based schemes.

### Attack cost estimates (Argon2id, 64 MiB, t=3)

A defender pays ~50-150 ms per phrase on typical hardware. Assuming an
attacker manages ~2,000 guesses/second per high-end GPU:

| Attack | Work | Time on 1 GPU | Time on 1,000 GPUs |
|--------|------|---------------|--------------------|
| Targeted collision, 5 words | 2^55 | ~570,000 years | ~570 years |
| Targeted collision, 4 words | 2^44 | ~280 years | ~100 days |
| Multi-target (10^6 lookup targets), 5 words | ~2^35 | ~200 days | ~5 hours |
| Multi-target (10^6 lookup targets), 8 words | ~2^68 | ~4.7 billion years | ~4.7 million years |

These estimates exclude key generation: each candidate address needs a real
keypair, which adds ~10 ms for Dilithium (Quantus) or ~10 µs for elliptic
curves per attempt. They also exclude the extra effort if the attacker wants
the colliding address to *look* similar to the target, which multiplies the
work by many orders of magnitude.

Run `cargo bench` to compare a bare SHA-256 checksum against Argon2id on your
hardware.

## Installation

### Rust

Add to your `Cargo.toml`:
```toml
[dependencies]
qp-human-checkphrase = { git = "https://github.com/Quantus-Network/human-checkphrase" }
```

```rust
use qp_human_checkphrase::{load_word_list, address_to_checksum, address_to_checksum_with_options};

let word_list = load_word_list()?;
let phrase = address_to_checksum("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", &word_list);
println!("{}", phrase.join("-")); // Cake-Stuff-Nerve-Job-Subway

// 8 words, domain-separated per chain
let phrase = address_to_checksum_with_options(
    "0x742d35Cc6634C0532925a3b844Bc9e7595f5bE21", &word_list, 8, Some("eip155:1"))?;
```

### JavaScript/TypeScript

```bash
npm install human-readable-checksum
```

```typescript
import { loadWordList, addressToChecksum } from "human-readable-checksum";

const wordList = loadWordList();
const checksum = await addressToChecksum("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", wordList);
console.log(checksum.join("-")); // Cake-Stuff-Nerve-Job-Subway

// 8 words, domain-separated per chain
const long = await addressToChecksum(address, wordList, { wordCount: 8, context: "eip155:1" });
```

### Dart

Add to your `pubspec.yaml`:
```yaml
dependencies:
  human_checksum:
    git:
      url: https://github.com/Quantus-Network/human-checkphrase
      path: dart
```

```dart
final checksum = HumanChecksum(wordList);
final words = checksum.addressToChecksum('1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa');

// 8 words, domain-separated per chain
final long = checksum.addressToChecksum(address, wordCount: 8, context: 'eip155:1');
```
