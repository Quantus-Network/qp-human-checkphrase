use criterion::{Criterion, black_box, criterion_group, criterion_main};
use human_readable_checksum::{address_to_checksum, load_bip39_list};
use sha2::{Digest, Sha256};

fn bench_checksum(c: &mut Criterion) {
	// Load BIP-39 list once (not part of the benchmark)
	let bip39_list = load_bip39_list().expect("Failed to load BIP-39 list");
	let address = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa";

	// Benchmark PBKDF2 (current method)
	c.bench_function("pbkdf2_40k", |b| {
		b.iter(|| black_box(address_to_checksum(black_box(address), &bip39_list)))
	});

	// Benchmark SHA-256 (alternative method)
	c.bench_function("sha256", |b| {
		b.iter(|| {
			let mut hasher = Sha256::new();
			hasher.update(black_box(address));
			let result = hasher.finalize();
			let key_int = u64::from_be_bytes([
				0, 0, result[0], result[1], result[2], result[3], result[4], result[5],
			]) >> 4;
			let key_int = key_int & ((1 << 44) - 1);
			let indices = [
				((key_int >> 33) & 0x7FF) as usize,
				((key_int >> 22) & 0x7FF) as usize,
				((key_int >> 11) & 0x7FF) as usize,
				(key_int & 0x7FF) as usize,
			];
			let words: Vec<String> = indices.iter().map(|&i| bip39_list[i].clone()).collect();
			black_box(words)
		})
	});
}

criterion_group!(benches, bench_checksum);
criterion_main!(benches);
