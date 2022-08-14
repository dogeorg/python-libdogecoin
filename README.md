# libdogecoin

A simple Python interface to interact with the libdogecoin C library written by the [Dogecoin Foundation](https://foundation.dogecoin.com/). This module contains wrappers for all user-facing address and transaction functions. For more information on usage of these wrappers, please refer to the bindings doc in the [Dogecoin Foundation libdogecoin repo](https://github.com/dogecoinfoundation/libdogecoin).

## Installation

To begin using the libdogecoin module, simply install libdogecoin using pip3:
```
pip3 install libdogecoin
```
Libdogecoin is now ready to be imported within your python script!

## API

All functions are prefixed with the letter "w" in order to differentiate between the Python wrapper functions and the redeclarations of the original C functions as required by Cython.

---
### w_context_start()
Start the secp256k1 context necessary for key pair generation. Must be started before calling any functions dealing with private or public keys.

---
### w_context_stop()
Stop the current instance of the secp256k1 context. It is advised to wait until the session is completely over before stopping the context.

---
### w_generate_priv_pub_key_pair(chain_code=0)
Generate a valid private key paired with the corresponding p2pkh address.

**Parameters:**
- chain_code -- 0 for mainnet pair, 1 for testnet pair

**Returns:**
- privkey -- the generated private key of the pair as byte string
- p2pkh_pubkey -- the generated public key of the pair as byte string

---
### w_generate_hd_master_pub_key_pair(chain_code=0)
Generate a master private and public key pair for use in hierarchical deterministic wallets. Public key can be used for child key derivation using w_generate_derived_hd_pub_key().

**Parameters:**
- chain_code -- 0 for mainnet pair, 1 for testnet pair

**Returns:**
- master_privkey -- the generated HD master private key of the pair as a byte string
- master_p2pkh_pubkey -- the generated HD master public key of the pair as a byte string

---
### w_generate_derived_hd_pub_key(wif_privkey_master)
Given a HD master public key, derive a child key from it.

**Parameters:**
- wif_privkey_master -- HD master private key as wif-encoded string

**Returns:**
- child_p2pkh_pubkey -- the resulting child public key derived from the provided HD master private key

---
### w_verify_priv_pub_keypair(wif_privkey, p2pkh_pubkey, chain_code=0)
Given a key private/public key pair, verify that the keys are valid and are associated with each other.

**Parameters:**
- wif_privkey -- string containing wif-encoded private key
- p2pkh_pubkey -- string containing address derived from wif_privkey
- chain_code -- 0 for mainnet, 1 for testnet

**Returns:**
- res -- 1 if the key pair is valid, 0 otherwise

---
### w_verify_master_priv_pub_keypair(wif_privkey_master, p2pkh_pubkey_master, chain_code=0)
Given a keypair from generate_hd_master_pub_key_pair, verify that the keys are valid and are associated with each other.

**Parameters:**
- wif_privkey_master -- string containing wif-encoded private master key
- p2pkh_pubkey_master -- string containing address derived from wif_privkey
- chain_code -- 0 for mainnet, 1 for testnet

**Returns:**
- res -- 1 if the master key pair is valid, 0 otherwise

---
### w_verify_p2pkh_address(p2pkh_pubkey)
Given a p2pkh address, confirm address is in correct Dogecoin format.

**Parameters:**
- p2pkh_pubkey -- string containing basic p2pkh address

**Returns:**
- res -- 1 if the address is valid, 0 otherwise.

---
### w_start_transaction()
Create a new, empty dogecoin transaction.

**Returns:**
- res -- the index of the newly created transaction in the session hash table

---
### w_add_utxo(tx_index, hex_utxo_txid, vout)
Given the index of a working transaction, add another input to it.

**Parameters:**
- tx_index -- the index of the working transaction to update
- hex_utxo_txid -- the transaction id of the utxo to be spent
- vout -- the number of outputs associated with the specified utxo

**Returns:**
- res -- 1 if the input was added successfully, 0 otherwise.

---
### w_add_output(tx_index, destination_address, amount)
Given the index of a working transaction, add another output to it.

**Parameters:**
- tx_index -- the index of the working transaction to update
- destination_address -- the address of the output being added
- amount -- the amount of dogecoin to send to the specified address

**Returns:**
- res -- 1 if the input was added successfully, 0 otherwise.

---
### w_finalize_transaction(tx_index, destination_address, subtracted_fee, out_dogeamount_for_verification, changeaddress)
Given the index of a working transaction, prepares it for signing by specifying the recipient and fee to subtract, directing extra change back to the sender.

**Parameters:**
- tx_index -- the index of the working transaction
- destination address -- the address to send coins to
- subtracted_fee -- the amount of dogecoin to assign as a fee
- out_dogeamount_for_verification -- the total amount of dogecoin being sent (fee included)
- changeaddress -- the address of the sender to receive their change

**Returns:**
- res -- the hex string representation of the transaction if successfully finalized, 0 otherwise

---
### w_get_raw_transaction(tx_index)
Given the index of a working transaction, returns the serialized object in hex format.

**Parameters:**
- tx_index -- the index of the working transaction

**Returns:**
- res -- the hex string representation of the transaction at index tx_index if it exists, 0 otherwise

---
### w_clear_transaction(tx_index)
Discard a working transaction.

**Parameters:**
- tx_index -- the index of the working transaction

---
### w_sign_raw_transaction(tx_index, incoming_raw_tx, script_hex, sig_hash_type, amount, privkey)
Sign a finalized raw transaction using the specified private key.

**Parameters:**
- tx_index -- the index of the working transaction to sign
- incoming_raw_tx -- the serialized string of the transaction to sign
- script_hex -- the hex of the script to be signed
- sig_hash_type -- the type of signature hash to be used
- amount -- the amount of dogecoin in the transaction being signed
- privkey -- the private key to sign with

**Returns:**
- res -- the hex string representation of the signed transaction if successfully signed, 0 otherwise.

---
### w_sign_transaction(tx_index, amounts, script_pubkey, privkey)
Sign all the inputs of a working transaction using the specified private key and public key script.

**Parameters:**
- tx_index -- the index of the working transaction to sign
- amounts -- an array of the input amounts in the specified transaction
- script_pubkey -- the pubkey script associated with the private key
- privkey -- the private key used to sign the specified transaction

**Returns:**
- res -- the hex string representation of the signed transaction if successfully signed, 0 otherwise.

---
### w_store_raw_transaction(incoming_raw_tx)
Stores a raw transaction at the next available index in the hash table.

**Parameters:**
- incoming_raw_tx -- the serialized string of the transaction to store.

**Returns:**
- res -- 1 if the transaction was stored successfully, 0 otherwise.
