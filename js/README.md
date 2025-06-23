# human_checksum

A Javascript implementation of human-readable checksums for cryptocurrency addresses using the BIP-39 word list and PBKDF2.

## Usage

```js
import 'package:human_checksum/human_checksum.dart';

void main() {
  // Load the BIP-39 word list (2048 words)
  final wordList = File('path/to/wordlist.txt').readAsLinesSync();

  final checksum = HumanChecksum(wordList);
  final address = '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa';

  final words = checksum.addressToChecksum(address);
  print(words.join('-')); // e.g. "museum-saddle-orphan-ribbon-peace"
}
```

## Installation

Add to your `pubspec.yaml`:

```yaml
dependencies:
  human_checksum:
    git:
      url: https://github.com/Resonance-Network/human-checksum.git
      path: dart
```

## License

MIT License - see LICENSE file
