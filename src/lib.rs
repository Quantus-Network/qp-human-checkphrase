use std::{
	fmt,
	fs::File,
	io::{self, BufRead, BufReader},
	path::Path,
};

use argon2::{Algorithm, Argon2, Params, Version};

// Constants
const WORD_LIST_FILE: &str = "final_wordlist.txt";
const WORD_LIST_SIZE: usize = 2048;

/// Scheme version string, also used as the Argon2 salt (optionally extended
/// with a domain-separation context: "human-checkphrase-v2|<context>").
pub const VERSION: &str = "human-checkphrase-v2";

// Argon2id parameters (RFC 9106). Memory-hardness is what keeps GPU/ASIC
// grinding attacks close to defender cost, so prefer raising memory over
// iterations if these are ever tuned.
const MEMORY_KIB: u32 = 64 * 1024;
const TIME_COST: u32 = 3;
const PARALLELISM: u32 = 1;

pub const DEFAULT_WORD_COUNT: usize = 5;
/// Argon2 output must be at least 4 bytes; 3 words -> 5 key bytes.
pub const MIN_WORD_COUNT: usize = 3;
/// 11 words = 121 bits, the most that fits in the u128 used for bit slicing.
pub const MAX_WORD_COUNT: usize = 11;

#[derive(Debug, PartialEq, Eq)]
pub enum ChecksumError {
	InvalidWordCount(usize),
	Kdf(String),
}

impl fmt::Display for ChecksumError {
	fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
		match self {
			ChecksumError::InvalidWordCount(n) => write!(
				f,
				"word count must be between {} and {}, got {}",
				MIN_WORD_COUNT, MAX_WORD_COUNT, n
			),
			ChecksumError::Kdf(e) => write!(f, "key derivation failed: {}", e),
		}
	}
}

impl std::error::Error for ChecksumError {}

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

	if words.len() != WORD_LIST_SIZE {
		return Err(io::Error::new(
			io::ErrorKind::InvalidData,
			format!("Word list must contain exactly {} words, found {}", WORD_LIST_SIZE, words.len()),
		));
	}

	Ok(words)
}

/// Canonicalize an address string before hashing.
///
/// Surrounding whitespace is stripped. 0x-prefixed hexadecimal addresses are
/// lowercased so that EIP-55 checksum casing does not change the checkphrase.
/// All other encodings (base58, bech32, SS58, ...) are case-sensitive and are
/// passed through unchanged; callers must supply them in canonical form.
pub fn normalize_address(address: &str) -> String {
	let trimmed = address.trim();
	let is_hex = trimmed.len() > 2
		&& (trimmed.starts_with("0x") || trimmed.starts_with("0X"))
		&& trimmed[2..].bytes().all(|b| b.is_ascii_hexdigit());
	if is_hex {
		trimmed.to_ascii_lowercase()
	} else {
		trimmed.to_string()
	}
}

/// Generate a checkphrase with the default word count (5) and no context.
///
/// Panics only if the word list is shorter than 2048 entries; use
/// [`load_word_list`] to obtain a validated list.
pub fn address_to_checksum(address: &str, word_list: &[String]) -> Vec<String> {
	address_to_checksum_with_options(address, word_list, DEFAULT_WORD_COUNT, None)
		.expect("default word count is valid")
}

/// Generate a checkphrase of `word_count` words, optionally domain-separated
/// by `context` (e.g. a chain id such as "eip155:1"). Two wallets must use
/// the same context string to see the same phrase for an address.
pub fn address_to_checksum_with_options(
	address: &str,
	word_list: &[String],
	word_count: usize,
	context: Option<&str>,
) -> Result<Vec<String>, ChecksumError> {
	if !(MIN_WORD_COUNT..=MAX_WORD_COUNT).contains(&word_count) {
		return Err(ChecksumError::InvalidWordCount(word_count));
	}

	let key_bytecount = (word_count * 11).div_ceil(8);
	let salt = match context {
		Some(ctx) if !ctx.is_empty() => format!("{}|{}", VERSION, ctx),
		_ => VERSION.to_string(),
	};

	// Argon2id: memory-hard KDF so that GPU/ASIC farms cannot grind
	// checkphrase collisions much faster than commodity hardware.
	let params = Params::new(MEMORY_KIB, TIME_COST, PARALLELISM, Some(key_bytecount))
		.map_err(|e| ChecksumError::Kdf(e.to_string()))?;
	let argon2 = Argon2::new(Algorithm::Argon2id, Version::V0x13, params);

	let mut key = vec![0u8; key_bytecount];
	argon2
		.hash_password_into(normalize_address(address).as_bytes(), salt.as_bytes(), &mut key)
		.map_err(|e| ChecksumError::Kdf(e.to_string()))?;

	// Convert key bytes to a big integer (u128 fits up to 11 words = 121 bits)
	let mut key_int = 0u128;
	for &byte in &key {
		key_int = (key_int << 8) | byte as u128;
	}

	// take only the first word_count * 11 bits
	key_int >>= (8 * key_bytecount) % 11;

	// Split into 11-bit indices and map to words
	let mut words = Vec::with_capacity(word_count);
	for i in 0..word_count {
		let shift = (word_count - 1 - i) * 11;
		let index = ((key_int >> shift) & 0x7FF) as usize;
		words.push(word_list[index].clone());
	}
	Ok(words)
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
		#[serde(rename = "wordCount")]
		word_count: Option<usize>,
		context: Option<String>,
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
			let word_count = case.word_count.unwrap_or(DEFAULT_WORD_COUNT);
			let checksum = address_to_checksum_with_options(
				&case.address,
				&word_list,
				word_count,
				case.context.as_deref(),
			)
			.expect("valid test vector options");

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
		assert_eq!(
			word_list.len(),
			WORD_LIST_SIZE,
			"Wordlist must have exactly {} words",
			WORD_LIST_SIZE
		);
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

	#[test]
	fn test_normalization() {
		// EIP-55 casing and surrounding whitespace must not change the phrase
		assert_eq!(
			normalize_address(" 0x742d35Cc6634C0532925a3b844Bc9e7595f5bE21\n"),
			"0x742d35cc6634c0532925a3b844bc9e7595f5be21"
		);
		assert_eq!(
			normalize_address("0X742D35CC6634C0532925A3B844BC9E7595F5BE21"),
			"0x742d35cc6634c0532925a3b844bc9e7595f5be21"
		);
		// base58 is case-sensitive and must pass through unchanged
		assert_eq!(
			normalize_address("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"),
			"1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
		);
		// non-hex 0x strings are not lowercased
		assert_eq!(normalize_address("0xNotHexZZZ"), "0xNotHexZZZ");
	}

	#[test]
	fn test_invalid_word_counts_rejected() -> io::Result<()> {
		let word_list = load_word_list()?;
		let address = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa";

		for bad in [0, MIN_WORD_COUNT - 1, MAX_WORD_COUNT + 1] {
			let result = address_to_checksum_with_options(address, &word_list, bad, None);
			assert_eq!(result, Err(ChecksumError::InvalidWordCount(bad)));
		}
		Ok(())
	}

	#[test]
	fn test_context_changes_phrase() -> io::Result<()> {
		let word_list = load_word_list()?;
		let address = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa";

		let plain =
			address_to_checksum_with_options(address, &word_list, DEFAULT_WORD_COUNT, None)
				.unwrap();
		let ctx = address_to_checksum_with_options(
			address,
			&word_list,
			DEFAULT_WORD_COUNT,
			Some("bitcoin"),
		)
		.unwrap();
		assert_ne!(plain, ctx, "Context should domain-separate phrases");

		let empty_ctx = address_to_checksum_with_options(
			address,
			&word_list,
			DEFAULT_WORD_COUNT,
			Some(""),
		)
		.unwrap();
		assert_eq!(plain, empty_ctx, "Empty context should equal no context");
		Ok(())
	}
}
