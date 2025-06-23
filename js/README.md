# human_checksum

A Javascript implementation of human-readable checksums for cryptocurrency addresses using the BIP-39 word list and PBKDF2.

## Usage

```ts
import { addressToChecksum, loadBip39List } from "human-readable-checksum";

const main = async () => {
  // Load the BIP-39 word list (2048 words)
  const wordList = await loadBip39List();
  const address = '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa';

  const checksum = addressToChecksum(address, wordList);

  console.log(checksum.join('-')); // e.g. "museum-saddle-orphan-ribbon-peace"
}
```

## Installation




## License

MIT License - see LICENSE file
