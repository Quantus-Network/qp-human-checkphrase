import 'dart:convert';
import 'package:pointycastle/export.dart';

class HumanChecksum {
  static const int wordListSize = 2048;

  /// Scheme version string, also used as the Argon2 salt (optionally extended
  /// with a domain-separation context: "human-checkphrase-v2|<context>").
  static const String version = 'human-checkphrase-v2';

  // Argon2id parameters (RFC 9106), must match all other implementations.
  static const int memoryKiB = 64 * 1024;
  static const int timeCost = 3;
  static const int parallelism = 1;

  static const int defaultWordCount = 5;

  /// Argon2 output must be at least 4 bytes; 3 words -> 5 key bytes.
  static const int minWordCount = 3;

  /// 11 words = 121 bits; keeps parity with the Rust implementation's u128.
  static const int maxWordCount = 11;

  final List<String> wordList;

  HumanChecksum(this.wordList) {
    if (wordList.length != wordListSize) {
      throw ArgumentError('Word list must contain exactly $wordListSize words');
    }
  }

  /// Canonicalize an address string before hashing.
  ///
  /// Surrounding whitespace is stripped. 0x-prefixed hexadecimal addresses
  /// are lowercased so that EIP-55 checksum casing does not change the
  /// checkphrase. All other encodings (base58, bech32, SS58, ...) are
  /// case-sensitive and are passed through unchanged; callers must supply
  /// them in canonical form.
  static String normalizeAddress(String address) {
    final trimmed = address.trim();
    if (RegExp(r'^0[xX][0-9a-fA-F]+$').hasMatch(trimmed)) {
      return trimmed.toLowerCase();
    }
    return trimmed;
  }

  /// Generate a checkphrase of [wordCount] words, optionally domain-separated
  /// by [context] (e.g. a chain id such as "eip155:1"). Two wallets must use
  /// the same context to see the same phrase for an address.
  List<String> addressToChecksum(
    String address, {
    int wordCount = defaultWordCount,
    String? context,
  }) {
    if (wordCount < minWordCount || wordCount > maxWordCount) {
      throw ArgumentError(
          'wordCount must be between $minWordCount and $maxWordCount, got $wordCount');
    }

    final keyByteCount = (wordCount * 11 + 7) ~/ 8;
    final salt =
        (context == null || context.isEmpty) ? version : '$version|$context';

    // Argon2id: memory-hard KDF so that GPU/ASIC farms cannot grind
    // checkphrase collisions much faster than commodity hardware.
    final params = Argon2Parameters(
      Argon2Parameters.ARGON2_id,
      utf8.encode(salt),
      version: Argon2Parameters.ARGON2_VERSION_13,
      iterations: timeCost,
      memory: memoryKiB,
      lanes: parallelism,
      desiredKeyLength: keyByteCount,
    );
    final generator = Argon2BytesGenerator()..init(params);
    final key = generator.process(utf8.encode(normalizeAddress(address)));

    // Convert key bytes to a big integer
    var keyInt = BigInt.zero;
    for (var byte in key) {
      keyInt = (keyInt << 8) | BigInt.from(byte);
    }

    // Take only the first wordCount * 11 bits
    keyInt = keyInt >> ((8 * keyByteCount) % 11);

    // Split into 11-bit indices
    final indices = <int>[];
    for (var i = 0; i < wordCount; i++) {
      final shift = (wordCount - 1 - i) * 11;
      final index = ((keyInt >> shift) & BigInt.from(0x7FF)).toInt();
      indices.add(index);
    }

    // Map to words
    return indices.map((i) => wordList[i]).toList();
  }
}
