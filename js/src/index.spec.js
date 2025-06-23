import { addressToChecksum, loadBip39List } from "./index.js";

const testAddresses = [
  "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", // Legit
  "1A1zP1eP5QGefi2DMPTfTL5SLmv7DixfNa", // Poisoned
];

describe("Generate a checksum from an address", () => {
  it("should fetch the bip39 list with 2048 words count", async () => {
    const wordList = await loadBip39List();

    expect(wordList.length).toBe(2048);
  });

  it("should return different checksum for different addresses even if only one char", async () => {
    const wordList = await loadBip39List();

    const checksum1 = addressToChecksum(testAddresses[0], wordList);
    const checksum2 = addressToChecksum(testAddresses[1], wordList);

    console.log("LEGIT, :", checksum1.join("-"));
    console.log("POISONED, :", checksum2.join("-"));

    expect(checksum1).not.toEqual(checksum2);
  });
});
