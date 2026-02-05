import { addressToChecksum, loadWordList } from "./index";

const testAddresses = [
  "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", // Legit
  "1A1zP1eP5QGefi2DMPTfTL5SLmv7DixfNa", // Poisoned
];

const expectedChecksums = [
  ["age", "awake", "secret", "blossom", "hedgehog"],
  ["innocent", "fitness", "joyful", "brown", "surge"],
];

describe("Generate a checksum from an address", () => {
  it("should load the word list with 2048 words count", () => {
    const wordList = loadWordList();

    expect(wordList.length).toBe(2048);
  });

  it("should generate same checksums as reference implementation", () => {
    const wordList = loadWordList();

    for (let i = 0; i < testAddresses.length; i++) {
      const checksum = addressToChecksum(testAddresses[i], wordList);
      console.log(`Address: ${testAddresses[i]}`);
      console.log(`Checksum: ${checksum.join("-")}`);
      expect(checksum).toEqual(expectedChecksums[i]);
    }
  });

  it("should return different checksum for different addresses even if only one char", () => {
    const wordList = loadWordList();

    const checksum1 = addressToChecksum(testAddresses[0], wordList);
    const checksum2 = addressToChecksum(testAddresses[1], wordList);

    expect(checksum1).not.toEqual(checksum2);
  });
});
