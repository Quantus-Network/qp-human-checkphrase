use std::{
	fs::File,
	io::{self, BufRead, BufReader},
	path::Path,
};

use pbkdf2::pbkdf2_hmac;
use sha2::Sha256;

// Constants
const WORD_LIST_FILE: &str = "final_wordlist.txt";
const WORD_COUNT: usize = 2048;
const SALT: &str = "human-readable-checksum";
const ITERATIONS: u32 = 40000;
const CHECKSUM_LEN: usize = 5;
const KEY_BYTECOUNT: usize = (CHECKSUM_LEN * 11).div_ceil(8);

pub fn load_word_list() -> io::Result<Vec<String>> {
	if !Path::new(WORD_LIST_FILE).exists() {
		return Err(io::Error::new(
			io::ErrorKind::NotFound,
			format!("Word list file '{}' not found", WORD_LIST_FILE),
		));
	}

	let file = File::open(WORD_LIST_FILE)?;
	let reader = BufReader::new(file);
	let words: Vec<String> = reader.lines().collect::<io::Result<_>>()?;

	if words.len() != WORD_COUNT {
		return Err(io::Error::new(
			io::ErrorKind::InvalidData,
			format!("Word list must contain exactly {} words, found {}", WORD_COUNT, words.len()),
		));
	}

	println!("Loaded {} words from {}", words.len(), WORD_LIST_FILE);
	Ok(words)
}

pub fn address_to_checksum(address: &str, word_list: &[String]) -> Vec<String> {
	// PBKDF2-HMAC-SHA256
	let mut key = [0u8; KEY_BYTECOUNT];
	pbkdf2_hmac::<Sha256>(address.as_bytes(), SALT.as_bytes(), ITERATIONS, &mut key);
	// println!("Key : {}", hex::encode(&key));

	// Convert key bytes to a big integer
	let mut key_int = 0u128; // Using u128 to handle larger checksum lengths
	for &byte in key.iter().take(KEY_BYTECOUNT) {
		key_int = (key_int << 8) | byte as u128;
	}

	// take only the first CHECKSUM_LEN * 11 bits
	key_int >>= (8 * KEY_BYTECOUNT) % 11;
	// println!("Key Int: {}", &key_int);
	// key_int &= (1 << (CHECKSUM_LEN * 11)) - 1;

	// Split into 11-bit indices
	let mut indices = Vec::with_capacity(CHECKSUM_LEN);
	for i in 0..CHECKSUM_LEN {
		let shift = (CHECKSUM_LEN - 1 - i) * 11;
		let index = ((key_int >> shift) & 0x7FF) as usize;
		indices.push(index);
	}
	// println!("Indexes: {:?}", indices);

	// Map to words
	indices.iter().map(|&i| word_list[i].clone()).collect()
}

#[cfg(test)]
mod tests {
	use super::*;
	use serde::Deserialize;
	use std::fs;

	const TEST_VECTORS_PATH: &str = "test-vectors/checksums.json";

	#[derive(Deserialize)]
	struct TestVectors {
		#[serde(rename = "testCases")]
		test_cases: Vec<TestCase>,
	}

	#[derive(Deserialize)]
	struct TestCase {
		address: String,
		description: String,
		expected: Vec<String>,
	}

	fn load_test_vectors() -> TestVectors {
		let content =
			fs::read_to_string(TEST_VECTORS_PATH).expect("Failed to read test vectors file");
		serde_json::from_str(&content).expect("Failed to parse test vectors JSON")
	}

	#[test]
	fn test_checksum_against_vectors() -> io::Result<()> {
		let word_list = load_word_list()?;
		let vectors = load_test_vectors();

		println!("Running {} test vectors...", vectors.test_cases.len());

		let mut passed = 0;
		let mut failed = 0;

		for case in &vectors.test_cases {
			let checksum = address_to_checksum(&case.address, &word_list);

			if checksum == case.expected {
				passed += 1;
			} else {
				failed += 1;
				println!("FAIL: {}", case.description);
				println!("  Address:  {}", case.address);
				println!("  Expected: {:?}", case.expected);
				println!("  Got:      {:?}", checksum);
			}
		}

		println!("\nResults: {} passed, {} failed", passed, failed);

		assert_eq!(failed, 0, "{} test vectors failed", failed);
		Ok(())
	}

	#[test]
	fn test_wordlist_size() -> io::Result<()> {
		let word_list = load_word_list()?;
		assert_eq!(word_list.len(), WORD_COUNT, "Wordlist must have exactly {} words", WORD_COUNT);
		Ok(())
	}

	#[test]
	fn test_deterministic() -> io::Result<()> {
		let word_list = load_word_list()?;
		let address = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa";

		let checksum1 = address_to_checksum(address, &word_list);
		let checksum2 = address_to_checksum(address, &word_list);

		assert_eq!(checksum1, checksum2, "Checksums should be deterministic");
		Ok(())
	}

	#[test]
	fn test_different_addresses_produce_different_checksums() -> io::Result<()> {
		let word_list = load_word_list()?;

		// These addresses differ by only one character
		let addr1 = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa";
		let addr2 = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DixfNa";

		let checksum1 = address_to_checksum(addr1, &word_list);
		let checksum2 = address_to_checksum(addr2, &word_list);

		assert_ne!(checksum1, checksum2, "Different addresses should produce different checksums");
		Ok(())
	}
}
