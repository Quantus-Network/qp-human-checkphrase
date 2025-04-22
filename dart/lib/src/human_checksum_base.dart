import 'dart:convert';
import 'dart:typed_data';
import 'package:crypto/crypto.dart';
import 'package:pointycastle/export.dart';

class HumanChecksum {
  static const int wordCount = 2048;
  static const String salt = 'human-readable-checksum';
  static const int iterations = 40000;
  static const int checksumLen = 5;
  static const int keyBytecount = (checksumLen * 11 + 7) ~/ 8;

  final List<String> wordList;

  HumanChecksum(this.wordList) {
    if (wordList.length != wordCount) {
      throw ArgumentError('Word list must contain exactly $wordCount words');
    }
  }

  List<String> addressToChecksum(String address) {
    // PBKDF2-HMAC-SHA256
    final params = Pbkdf2Parameters(utf8.encode(salt), iterations, keyBytecount);
    final pbkdf2 = PBKDF2KeyDerivator(HMac(SHA256Digest(), 64));
    pbkdf2.init(params);

    final key = pbkdf2.process(utf8.encode(address));

    // Convert key bytes to a big integer
    var keyInt = BigInt.zero;
    for (var byte in key) {
      keyInt = (keyInt << 8) | BigInt.from(byte);
    }

    // Take only the first checksumLen * 11 bits
    keyInt = keyInt >> ((8 * keyBytecount) % 11);

    // Split into 11-bit indices
    final indices = <int>[];
    for (var i = 0; i < checksumLen; i++) {
      final shift = (checksumLen - 1 - i) * 11;
      final index = ((keyInt >> shift) & BigInt.from(0x7FF)).toInt();
      indices.add(index);
    }

    // Map to words
    return indices.map((i) => wordList[i]).toList();
  }
}
