# human-checkphrase

A tool to generate human-readable checksums from cryptocurrency addresses using a curated positive wordlist and PBKDF2. 
Designed to make address verification easier and prevent address poisoning attacks—where attackers craft lookalike addresses to trick users, this tool can be used with any existing blockchain address. Users viewing an address can also be presented with a unique, memorable phrase.

## Examples

| Address | Chain | Checkphrase |
|---------|-------|-------------|
| `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa` | Bitcoin | Age-Awake-Secret-Blossom-Hedgehog |
| `1A1zP1eP5QGefi2DMPTfTL5SLmv7DixfNa` | Bitcoin (poisoned) | Innocent-Fitness-Joyful-Brown-Surge |
| `0x742d35Cc6634C0532925a3b844Bc9e7595f5bE21` | Ethereum | Donkey-Crucial-Beach-Offer-Expire |
| `5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY` | Polkadot | Merge-Boss-Syrup-Inestimable-Toss |
| `cosmos1hsk6jryyqjfhp5dhc55tc9jtckygx0eph6dd02` | Cosmos | Find-Frog-Basic-Reopen-Another |
| `bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq` | Bitcoin (bech32) | View-Start-Satisfy-Immense-Clown |
| `qzk7h3xH4Fmv2RqKpN8sT5jW9cY6gB1dL3mX0vQwEaUoZrJtS` | Quantus | Unveil-Butter-Always-Since-Schnorr |
| `qzkABCDEF123456789abcdefGHIJKLMNOPQRSTUVWXYZ000001` | Quantus | Patch-Invite-Split-Surface-Dial |
| `qzkXyZ987654321FeDcBaAbCdEfGhIjKlMnOpQrStUvWxYz99` | Quantus | Important-Extend-Barely-Close-Text |

Notice how the first two Bitcoin addresses differ by only one character (`v` vs `x`) but produce completely different checkphrases—this is exactly what helps prevent address poisoning attacks.

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

## This repo contains

- **Rust**: A library crate at the root for fast, reusable checksum generation
- **JavaScript/TypeScript**: NPM package in `js/`
- **Dart**: Pub package in `dart/`
- **Python**: Prototype scripts in `scripts/` for experimentation and reference

### Running tests

```bash
./run_tests.sh
```

Or run individually:
- Rust: `cargo test -- --nocapture`
- JavaScript: `cd js && npm test`
- Dart: `cd dart && dart test`

## Security Analysis

Each of the words has 2048 (2^11) choices so if we choose 5 words, we have a total set of 2^55 ~ 36 quadrillion possible combinations. 
The parameters for PBKDF2 are chosen to enable fast UI generation while still requiring an attacker to do ~50000x more work to generate rainbow tables. 
Run `cargo bench` to see the comparison of doing just SHA256 to generate the checksum vs using PBKDF2.

On a typical MacBook, a single SHA256 hash takes ~262ns, so the time to generate an entire rainbow table (single-threaded CPU) would be:
`2^55 * 262ns ≈ 300 years`

With PBKDF2 (40,000 iterations), each checksum takes ~14ms, so a rainbow table would take:
`2^55 * 14ms ≈ 16 million years`

A high-end GPU can compute SHA256 ~10x faster than a CPU, reducing each PBKDF2 call to ~1.4ms. Even then:
`2^55 * 1.4ms ≈ 1.6 million years` per GPU

With a cluster of 1,000 GPUs working in parallel: ~1,600 years.


This of course does not include the time it takes to generate a private key, derive a public key and address from it, which can add another 10ms for dilithium keys (nearly doubling) or 10 us for elliptic curves. 
It also does not take into account if the attacker wants a similar looking address in addition to the same checksum, which multiplies the required effort by many orders of magnitude.

Using 4 words still provides a fair bit of security, `2**44 * 14 / 1000 / 60 / 60 / 24 / 365` or ~7800 years on a single CPU.

## Installation

### Rust

Add to your `Cargo.toml`:
```toml
[dependencies]
human_readable_checksum = { git = "https://github.com/Quantus-Network/human-checkphrase" }
```

### JavaScript/TypeScript

```bash
npm install human-readable-checksum
```

```typescript
import { loadWordList, addressToChecksum } from "human-readable-checksum";

const wordList = loadWordList();
const checksum = addressToChecksum("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", wordList);
console.log(checksum.join("-")); // Age-Awake-Secret-Blossom-Hedgehog
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