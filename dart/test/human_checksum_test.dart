import 'dart:io';
import 'package:test/test.dart';
import 'package:human_checksum/human_checksum.dart';

void main() {
  late List<String> wordList;
  late HumanChecksum humanChecksum;

  setUp(() {
    // Load the word list from the bundled asset
    final file = File('../crypto_checksum_bip39.txt');
    wordList = file.readAsLinesSync();
    humanChecksum = HumanChecksum(wordList);
  });

  test('generates same checksums as reference implementation', () {
    final testAddresses = [
      '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa', // Legit
      '1A1zP1eP5QGefi2DMPTfTL5SLmv7DixfNa', // Poisoned
    ];

    // These values should match the output from the Rust and Python implementations
    final expectedChecksums = [
      ['alarm', 'banana', 'secret', 'border', 'horror'],
      ['join', 'flower', 'lamp', 'busy', 'summer'],
    ];

    for (var i = 0; i < testAddresses.length; i++) {
      final checksum = humanChecksum.addressToChecksum(testAddresses[i]);
      print('Address: ${testAddresses[i]}');
      print('Checksum: ${checksum.join('-')}');
      // Uncomment after adding expected values:
      expect(checksum, equals(expectedChecksums[i]));
    }
  });

  test('generates consistent checksums', () {
    final address = '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa';
    final firstChecksum = humanChecksum.addressToChecksum(address);
    final secondChecksum = humanChecksum.addressToChecksum(address);
    expect(firstChecksum, equals(secondChecksum));
  });

  test('generates different checksums for similar addresses', () {
    final address1 = '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa';
    final address2 = '1A1zP1eP5QGefi2DMPTfTL5SLmv7DixfNa';
    final checksum1 = humanChecksum.addressToChecksum(address1);
    final checksum2 = humanChecksum.addressToChecksum(address2);
    // expect known checksums same as the other implementations.
    expect(checksum1, equals(['alarm', 'banana', 'secret', 'border', 'horror']));
    expect(checksum2, equals(['join', 'flower', 'lamp', 'busy', 'summer']));
  });
}
