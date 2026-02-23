import { addressToChecksum, loadWordList } from "./index";
import { readFileSync } from "fs";
import { join } from "path";

interface TestCase {
  address: string;
  description: string;
  expected: string[];
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

  it("should pass all test vectors", () => {
    console.log(`Running ${testVectors.testCases.length} test vectors...`);

    let passed = 0;
    let failed = 0;

    for (const testCase of testVectors.testCases) {
      const checksum = addressToChecksum(testCase.address, wordList);

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
  });

  it("should generate deterministic checksums", () => {
    const address = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa";
    const checksum1 = addressToChecksum(address, wordList);
    const checksum2 = addressToChecksum(address, wordList);

    expect(checksum1).toEqual(checksum2);
  });

  it("should return different checksum for different addresses even if only one char differs", () => {
    const addr1 = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa";
    const addr2 = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DixfNa";

    const checksum1 = addressToChecksum(addr1, wordList);
    const checksum2 = addressToChecksum(addr2, wordList);

    expect(checksum1).not.toEqual(checksum2);
  });
});
