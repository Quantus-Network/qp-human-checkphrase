import 'dart:convert';
import 'dart:io';
import 'package:test/test.dart';
import 'package:human_checksum/human_checksum.dart';

class TestCase {
  final String address;
  final String description;
  final List<String> expected;
  final int? wordCount;
  final String? context;

  TestCase({
    required this.address,
    required this.description,
    required this.expected,
    this.wordCount,
    this.context,
  });

  factory TestCase.fromJson(Map<String, dynamic> json) {
    return TestCase(
      address: json['address'] as String,
      description: json['description'] as String,
      expected: (json['expected'] as List).cast<String>(),
      wordCount: json['wordCount'] as int?,
      context: json['context'] as String?,
    );
  }
}

class TestVectors {
  final String version;
  final String description;
  final List<TestCase> testCases;

  TestVectors({
    required this.version,
    required this.description,
    required this.testCases,
  });

  factory TestVectors.fromJson(Map<String, dynamic> json) {
    return TestVectors(
      version: json['version'] as String,
      description: json['description'] as String,
      testCases: (json['testCases'] as List)
          .map((e) => TestCase.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}

TestVectors loadTestVectors() {
  final file = File('../test-vectors/checksums.json');
  final content = file.readAsStringSync();
  final json = jsonDecode(content) as Map<String, dynamic>;
  return TestVectors.fromJson(json);
}

void main() {
  late List<String> wordList;
  late HumanChecksum humanChecksum;
  late TestVectors testVectors;

  setUp(() {
    // Load the word list from the bundled asset
    final file = File('../final_wordlist.txt');
    wordList = file.readAsLinesSync();
    humanChecksum = HumanChecksum(wordList);
    testVectors = loadTestVectors();
  });

  test('wordlist has 2048 words', () {
    expect(wordList.length, equals(2048));
  });

  test('passes all test vectors', () {
    print('Running ${testVectors.testCases.length} test vectors...');

    var passed = 0;
    var failed = 0;

    for (final testCase in testVectors.testCases) {
      final checksum = humanChecksum.addressToChecksum(
        testCase.address,
        wordCount: testCase.wordCount ?? HumanChecksum.defaultWordCount,
        context: testCase.context,
      );

      if (checksum.join(',') == testCase.expected.join(',')) {
        passed++;
      } else {
        failed++;
        print('FAIL: ${testCase.description}');
        print('  Address:  ${testCase.address}');
        print('  Expected: ${testCase.expected}');
        print('  Got:      $checksum');
      }
    }

    print('\nResults: $passed passed, $failed failed');
    expect(failed, equals(0));
  }, timeout: Timeout(Duration(minutes: 15)));

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
    expect(checksum1, isNot(equals(checksum2)));
  });

  test('normalizes hex addresses and whitespace but not base58', () {
    expect(
      HumanChecksum.normalizeAddress(
          ' 0x742d35Cc6634C0532925a3b844Bc9e7595f5bE21\n'),
      equals('0x742d35cc6634c0532925a3b844bc9e7595f5be21'),
    );
    expect(
      HumanChecksum.normalizeAddress(
          '0X742D35CC6634C0532925A3B844BC9E7595F5BE21'),
      equals('0x742d35cc6634c0532925a3b844bc9e7595f5be21'),
    );
    expect(
      HumanChecksum.normalizeAddress('1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa'),
      equals('1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa'),
    );
    expect(HumanChecksum.normalizeAddress('0xNotHexZZZ'), equals('0xNotHexZZZ'));
  });

  test('rejects invalid word counts', () {
    final address = '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa';
    expect(() => humanChecksum.addressToChecksum(address, wordCount: 2),
        throwsArgumentError);
    expect(() => humanChecksum.addressToChecksum(address, wordCount: 12),
        throwsArgumentError);
  });

  test('domain-separates phrases by context', () {
    final address = '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa';
    final plain = humanChecksum.addressToChecksum(address);
    final withContext =
        humanChecksum.addressToChecksum(address, context: 'bitcoin');
    expect(withContext, isNot(equals(plain)));
  });
}
