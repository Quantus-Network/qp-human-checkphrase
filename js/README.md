# human_checksum

A JavaScript implementation of human-readable checkphrases for cryptocurrency addresses using a curated 2048-word list and Argon2id.

## Usage

```ts
import { addressToChecksum, loadWordList } from "human-readable-checksum";

const main = async () => {
  // Load the word list (2048 words)
  const wordList = loadWordList();
  const address = '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa';

  const checksum = await addressToChecksum(address, wordList);
  console.log(checksum.join('-')); // "cake-stuff-nerve-job-subway"

  // Optional: longer phrase, domain-separated per chain
  const long = await addressToChecksum(address, wordList, {
    wordCount: 8,
    context: 'bitcoin',
  });
}
```

Addresses are normalized before hashing: surrounding whitespace is stripped and
`0x`-prefixed hex addresses are lowercased (so EIP-55 casing does not change the
phrase). Other encodings must be passed in canonical form.

## Installation

```shell
npm i git+https://github.com/Quantus-Network/human-checkphrase.git#main:js
```


## License

MIT License - see LICENSE file
