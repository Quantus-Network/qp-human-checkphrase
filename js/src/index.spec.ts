import { addressToChecksum, loadWordList, normalizeAddress } from "./index";
import { readFileSync } from "fs";
import { join } from "path";

interface TestCase {
  address: string;
  description: string;
  expected: string[];
  wordCount?: number;
  context?: string;
}

interface TestVectors {
  version: string;
  description: string;
  testCases: TestCase[];
}

function loadTestVectors(): TestVectors {
  // Tests are run from the js/ directory, so go up one level to repo root
  const vectorsPath = join(process.cwd(), "..", "test-vectors", "checksums.json");
  const content = readFileSync(vectorsPath, "utf-8");
  return JSON.parse(content);
}

describe("Generate a checksum from an address", () => {
  const wordList = loadWordList();
  const testVectors = loadTestVectors();

  it("should load the word list with 2048 words count", () => {
    expect(wordList.length).toBe(2048);
  });

  it("should pass all test vectors", async () => {
    console.log(`Running ${testVectors.testCases.length} test vectors...`);

    let passed = 0;
    let failed = 0;

    for (const testCase of testVectors.testCases) {
      const checksum = await addressToChecksum(testCase.address, wordList, {
        wordCount: testCase.wordCount,
        context: testCase.context,
      });

      if (JSON.stringify(checksum) === JSON.stringify(testCase.expected)) {
        passed++;
      } else {
        failed++;
        console.log(`FAIL: ${testCase.description}`);
        console.log(`  Address:  ${testCase.address}`);
        console.log(`  Expected: ${JSON.stringify(testCase.expected)}`);
        console.log(`  Got:      ${JSON.stringify(checksum)}`);
      }
    }

    console.log(`\nResults: ${passed} passed, ${failed} failed`);
    expect(failed).toBe(0);
  }, 120_000);

  it("should generate deterministic checksums", async () => {
    const address = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa";
    const checksum1 = await addressToChecksum(address, wordList);
    const checksum2 = await addressToChecksum(address, wordList);

    expect(checksum1).toEqual(checksum2);
  }, 30_000);

  it("should return different checksum for different addresses even if only one char differs", async () => {
    const addr1 = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa";
    const addr2 = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DixfNa";

    const checksum1 = await addressToChecksum(addr1, wordList);
    const checksum2 = await addressToChecksum(addr2, wordList);

    expect(checksum1).not.toEqual(checksum2);
  }, 30_000);

  it("should normalize hex addresses and whitespace but not base58", () => {
    expect(normalizeAddress(" 0x742d35Cc6634C0532925a3b844Bc9e7595f5bE21\n")).toBe(
      "0x742d35cc6634c0532925a3b844bc9e7595f5be21",
    );
    expect(normalizeAddress("0X742D35CC6634C0532925A3B844BC9E7595F5BE21")).toBe(
      "0x742d35cc6634c0532925a3b844bc9e7595f5be21",
    );
    expect(normalizeAddress("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")).toBe(
      "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
    );
    expect(normalizeAddress("0xNotHexZZZ")).toBe("0xNotHexZZZ");
  });

  it("should reject invalid word counts", async () => {
    const address = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa";
    await expect(
      addressToChecksum(address, wordList, { wordCount: 2 }),
    ).rejects.toThrow(RangeError);
    await expect(
      addressToChecksum(address, wordList, { wordCount: 12 }),
    ).rejects.toThrow(RangeError);
  });

  it("should domain-separate phrases by context", async () => {
    const address = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa";
    const plain = await addressToChecksum(address, wordList);
    const withContext = await addressToChecksum(address, wordList, {
      context: "bitcoin",
    });

    expect(withContext).not.toEqual(plain);
  }, 30_000);
});
