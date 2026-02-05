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

	#[test]
	fn test_checksum() -> io::Result<()> {
		let bip39_list = load_word_list()?;
		let combos = (bip39_list.len() as u64).pow(CHECKSUM_LEN as u32);
		println!("Total combos: {}", combos);
		println!(
			"Sample: {:?} ... {:?}",
			&bip39_list[..CHECKSUM_LEN],
			&bip39_list[bip39_list.len() - CHECKSUM_LEN..]
		);

		let test_addresses = [
			"1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", // Legit
			"1A1zP1eP5QGefi2DMPTfTL5SLmv7DixfNa", // Poisoned
		];
		for addr in test_addresses {
			let four_words = address_to_checksum(addr, &bip39_list);
			println!("Address: {}", addr);
			println!("Checksum: {}", four_words.join("-"));
		}

		Ok(())
	}
}
