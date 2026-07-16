# human_checksum

A Dart implementation of human-readable checkphrases for cryptocurrency addresses using a curated 2048-word list and Argon2id.

## Usage

```dart
import 'package:human_checksum/human_checksum.dart';

void main() {
  // Load the word list (2048 words)
  final wordList = File('path/to/wordlist.txt').readAsLinesSync();

  final checksum = HumanChecksum(wordList);
  final address = '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa';

  final words = checksum.addressToChecksum(address);
  print(words.join('-')); // "cake-stuff-nerve-job-subway"

  // Optional: longer phrase, domain-separated per chain
  final long = checksum.addressToChecksum(address, wordCount: 8, context: 'bitcoin');
}
```

Addresses are normalized before hashing: surrounding whitespace is stripped and
`0x`-prefixed hex addresses are lowercased (so EIP-55 casing does not change the
phrase). Other encodings must be passed in canonical form.

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
