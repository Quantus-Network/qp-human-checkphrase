# human-checksum

A tool to generate human-readable checksums from cryptocurrency addresses using the BIP-39 word list and PBKDF2. 
Designed to make address verification easier and prevent address poisoning attacks—where attackers craft lookalike addresses to trick users, this tool can be used with any existing blockchain address. Users viewing an address can also be presented with a unique, memorable phrase. Some examples:

Address:
qzpCoRjvHcnH8VnbS2qMYu41xR9m3Qq2kcKhXEFpPHu6oHW6h

Checkphrase:Arrest-Enemy-Around-Answer-Clump

Address:
qznYAYX6TQKGhKPL8fGF7aSp8NvAm7x42SEctxUk35qnx6Psp

Checkphrase:Upgrade-Duck-Select-Stove-Seminar

Address:
qzmbBbKgb94F42UXjNCtNsC5JTS1taKSsit3xwda1JD3LU3dB

Checkphrase:Circle-Above-Scheme-Load-Alarm

This repo contains:
Rust: A library crate (human-readable-checksum) at the root for fast, reusable checksum generation.

Python: Prototype scripts in scripts/ for experimentation and reference.

Run `cargo test -- --nocapture` to see words derived from some example addresses

Run `cd scripts && pip install -r requirements.txt && python ./words.py` to see the python equivalent

## Security Analysis

Each of the words has 2048 (2**11) choices (length of BIP-39 word list) so if we choose 5 words, we have a total set of 2**55 ~ 36Q possible combinations. 
The parameters for PBKDF2 are chosen to enable fast UI generation while still requiring an attacker to do ~50000x more work to generate rainbow tables. 
Run `cargo bench` to see the comparison of doing just SHA256 to generate the checksum vs using PBKDF2.

On a typical macbook, we have SHA256 taking 262.37ns, so the time to generate an entire rainbow table on a CPU, single threaded would be
`2**55 * 262.37 / 1000000000 / 60 / 60 / 24 / 365` which is about 300 years. One PBKDF2 generation takes about 14ms, so to generate 
a rainbow table for the PBKDF2 version would take
`2**55 * 14 / 1000 / 60 / 60 / 24 / 365` which is about 16M years.
Hardware optimization for GPU might push the iteration time for PBKDF2 down to 10ns, which puts us at
`2**55 * 40000 / 100000000 / 60 / 60 / 24 / 365` or 450K years for a single GPU. 

This of course does not include the time it takes to generate a private key, derive a public key and address from it, 
which can add another 10ms for dilithium keys (nearly doubling) or 10 us for elliptic curves. 
It also does not take into account if the attacker wants a similar looking address in addition to the same checksum, which
multiplies the required effort by many orders of magnitude.

Using 4 words still provides a fair bit of security, `2**44 * 14 / 1000 / 60 / 60 / 24 / 365` or ~7800 years on a single CPU.

## Importing
simply add `human_readable_checksum = { git = "https://github.com/Resonance-Network/human-checksum" }` to the dependencies section of your Cargo.toml