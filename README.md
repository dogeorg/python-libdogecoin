# libdogecoin

A Python interface to the [libdogecoin](https://github.com/dogecoinfoundation/libdogecoin) C library, maintained by the [Dogecoin Foundation](https://foundation.dogecoin.com/). Provides wrappers for all user-facing address and transaction functions via a [CFFI](https://cffi.readthedocs.io/) extension that links the static library at build time — no shared `.so`/`.dll` dependency at runtime.

## Supported platforms

| Platform | Wheel tag |
|----------|-----------|
| Linux x86\_64 | `manylinux2014_x86_64` |
| Linux i686 | `manylinux2014_i686` |
| Linux aarch64 | `manylinux2014_aarch64` |
| Linux armv7l | `manylinux2014_armv7l` |
| macOS x86\_64 | `macosx_10_9_x86_64` |
| Windows x86\_64 | `win_amd64` |
| Windows i686 | `win32` |

## Installation

```
pip install libdogecoin
```

## Quick start

```python
from libdogecoin import w_context_start, w_context_stop, w_generate_priv_pub_key_pair

w_context_start()
privkey, address = w_generate_priv_pub_key_pair()
print(privkey, address)
w_context_stop()
```

## API

All functions are prefixed with `w_` to distinguish the Python wrappers from the underlying C symbols.

---
### w_context_start()
Start the secp256k1 context. Must be called before any key or address operation.

---
### w_context_stop()
Stop the secp256k1 context.

---
### w_generate_priv_pub_key_pair(chain_code=0, as_bytes=False)
Generate a WIF private key and matching p2pkh address.

**Parameters:**
- `chain_code` — 0 for mainnet, 1 for testnet
- `as_bytes` — if True, return raw bytes instead of strings

**Returns:** `(privkey, p2pkh_pubkey)`

---
### w_generate_hd_master_pub_key_pair(chain_code=0, as_bytes=False)
Generate an HD master private key and matching p2pkh address.

**Parameters:**
- `chain_code` — 0 for mainnet, 1 for testnet
- `as_bytes` — if True, return raw bytes instead of strings

**Returns:** `(master_privkey, master_p2pkh_pubkey)`

---
### w_generate_derived_hd_pub_key(wif_privkey_master, as_bytes=False)
Derive a child p2pkh address from an HD master private key.

**Parameters:**
- `wif_privkey_master` — HD master private key (WIF-encoded string)
- `as_bytes` — if True, return raw bytes

**Returns:** `child_p2pkh_pubkey`

---
### w_verify_priv_pub_keypair(wif_privkey, p2pkh_pubkey, chain_code=0)
Verify that a WIF private key and p2pkh address form a valid pair.

**Parameters:**
- `wif_privkey` — WIF-encoded private key
- `p2pkh_pubkey` — p2pkh address derived from `wif_privkey`
- `chain_code` — 0 for mainnet, 1 for testnet

**Returns:** `True` if valid, `False` otherwise

---
### w_verify_master_priv_pub_keypair(wif_privkey_master, p2pkh_pubkey_master, chain_code=0)
Verify that an HD master key pair is valid and consistent.

**Parameters:**
- `wif_privkey_master` — WIF-encoded HD master private key
- `p2pkh_pubkey_master` — p2pkh address derived from the master key
- `chain_code` — 0 for mainnet, 1 for testnet

**Returns:** `True` if valid, `False` otherwise

---
### w_verify_p2pkh_address(p2pkh_pubkey)
Validate that a string is a well-formed Dogecoin p2pkh address.

**Parameters:**
- `p2pkh_pubkey` — p2pkh address string

**Returns:** `True` if valid, `False` otherwise

---
### w_start_transaction()
Create a new empty working transaction.

**Returns:** `tx_index` — integer index of the new transaction

---
### w_add_utxo(tx_index, hex_utxo_txid, vout)
Add a UTXO input to a working transaction.

**Parameters:**
- `tx_index` — index of the working transaction
- `hex_utxo_txid` — transaction id of the UTXO to spend
- `vout` — output index within that transaction

**Returns:** 1 on success, 0 on failure

---
### w_add_output(tx_index, destination_address, amount)
Add an output to a working transaction.

**Parameters:**
- `tx_index` — index of the working transaction
- `destination_address` — recipient p2pkh address
- `amount` — amount of Dogecoin to send (string or number)

**Returns:** 1 on success, 0 on failure

---
### w_finalize_transaction(tx_index, destination_address, subtracted_fee, out_dogeamount_for_verification, changeaddress)
Finalise a working transaction, deducting the fee and routing change back to the sender.

**Parameters:**
- `tx_index` — index of the working transaction
- `destination_address` — primary recipient address
- `subtracted_fee` — fee to deduct (string or number)
- `out_dogeamount_for_verification` — total amount being sent including fee
- `changeaddress` — sender's address to receive change

**Returns:** raw hex string of the transaction, or 0 on failure

---
### w_get_raw_transaction(tx_index)
Return the serialised hex of a working transaction.

**Parameters:**
- `tx_index` — index of the working transaction

**Returns:** hex string, or 0 if not found

---
### w_clear_transaction(tx_index)
Discard a working transaction.

**Parameters:**
- `tx_index` — index of the working transaction

---
### w_sign_raw_transaction(tx_index, incoming_raw_tx, script_hex, sig_hash_type, privkey)
Sign one input of a raw transaction in place.

**Parameters:**
- `tx_index` — input index to sign (0-based)
- `incoming_raw_tx` — serialised hex of the transaction
- `script_hex` — scriptPubKey hex of the input being signed
- `sig_hash_type` — signature hash type (typically 1)
- `privkey` — WIF-encoded signing key

**Returns:** hex string of the (partially) signed transaction, or 0 on failure

---
### w_sign_transaction(tx_index, script_pubkey, privkey)
Sign all inputs of a working transaction.

**Parameters:**
- `tx_index` — index of the working transaction
- `script_pubkey` — scriptPubKey hex associated with the inputs
- `privkey` — WIF-encoded signing key

**Returns:** 1 if all inputs were signed, 0 otherwise

---
### w_store_raw_transaction(incoming_raw_tx)
Store a pre-built raw transaction in the session table.

**Parameters:**
- `incoming_raw_tx` — serialised hex string (max 100 KB)

**Returns:** index of the stored transaction, or 0 if too large

---
### w_remove_all()
Clear all working transactions from the session table.

---
### w_get_derived_hd_address(masterkey, account, ischange, addressindex, outprivkey=False)
Derive a HD extended key at a given account/change/index path.

**Parameters:**
- `masterkey` — HD master private key (WIF-encoded)
- `account` — BIP44 account number
- `ischange` — 0 for external chain, 1 for internal/change
- `addressindex` — address index
- `outprivkey` — if True, return the extended private key; otherwise the extended public key

**Returns:** extended public key (xpub) string, or extended private key (xprv) when `outprivkey=True`

---
### w_get_derived_hd_address_by_path(masterkey, derived_path, outprivkey=False)
Derive a HD extended key at an explicit BIP32 derivation path.

**Parameters:**
- `masterkey` — HD master private key (WIF-encoded)
- `derived_path` — BIP32 path string (e.g. `"m/44'/3'/0'/0/0"`)
- `outprivkey` — if True, return the extended private key; otherwise the extended public key

**Returns:** extended public key (xpub) or extended private key (xprv) string

---
### w_generate_random_english_mnemonic(size)
Generate a cryptographically random BIP39 English mnemonic phrase.

**Parameters:**
- `size` — entropy bit length as a string: `"128"`, `"160"`, `"192"`, `"224"`, or `"256"`

**Returns:** mnemonic phrase string (12–24 words), or `None` on failure

---
### w_generate_english_mnemonic(entropy, size)
Generate a BIP39 English mnemonic from caller-supplied hex entropy.

**Parameters:**
- `entropy` — hex-encoded entropy string
- `size` — entropy bit length as a string (same values as above)

**Returns:** mnemonic phrase string, or `None` on failure

---
### w_dogecoin_seed_from_mnemonic(mnemonic, passphrase="")
Derive a 64-byte BIP32 master seed from a BIP39 mnemonic.

**Parameters:**
- `mnemonic` — BIP39 mnemonic phrase
- `passphrase` — optional BIP39 passphrase (default `""`)

**Returns:** `bytes` of length 64, or `None` on failure

---
### w_get_derived_hd_address_from_mnemonic(account, index, change_level, mnemonic, passphrase="", chain_code=0)
Derive a spendable p2pkh address directly from a BIP39 mnemonic phrase.

**Parameters:**
- `account` — BIP44 account number
- `index` — address index
- `change_level` — `"0"` for external (receiving), `"1"` for internal (change)
- `mnemonic` — BIP39 mnemonic phrase
- `passphrase` — optional BIP39 passphrase
- `chain_code` — 0 for mainnet, 1 for testnet

**Returns:** p2pkh address string, or `None` on failure

---
### w_sign_message(privkey, message)
Sign an arbitrary message with a WIF private key.

**Parameters:**
- `privkey` — WIF-encoded private key
- `message` — message string to sign

**Returns:** base64-encoded signature string, or `None` on failure

---
### w_verify_message(signature, message, address)
Verify a signed message against a p2pkh address.

**Parameters:**
- `signature` — base64-encoded signature (from `w_sign_message`)
- `message` — the original message string
- `address` — the p2pkh address corresponding to the signing key

**Returns:** `True` if valid, `False` otherwise

---
### w_qrgen_p2pkh_to_qr_string(p2pkh)
Return a text-art QR code string for a p2pkh address.

**Returns:** multi-line string, or `None` on failure

---
### w_qrgen_p2pkh_consoleprint_to_qr(p2pkh)
Print a QR code for a p2pkh address to stdout.

---
### w_qrgen_string_to_qr_pngfile(filename, data, size_multiplier=4)
Write a QR code as a PNG file.

**Returns:** 1 on success, 0 on failure

---
### w_qrgen_string_to_qr_jpgfile(filename, data, size_multiplier=4)
Write a QR code as a JPEG file.

**Returns:** 1 on success, 0 on failure

---
### available()
Return the list of libdogecoin C function names present in this wheel's build.

**Returns:** `list[str]`

```python
from libdogecoin import available
print(available())
# ['dogecoin_ecc_start', 'dogecoin_ecc_stop', 'generatePrivPubKeypair', ...]
```

## Building from source

Requires a C compiler, `autoconf`, `automake`, and `libtool` (for the source-build fallback).

```bash
pip install cffi requests build
python fetch.py --host=x86_64-pc-linux-gnu   # populates lib/ and include/
python -m build -w
```

`fetch.py` probes the libdogecoin GitHub releases for a pre-built binary for the requested host triplet and falls back to an autotools source build if none is available.
