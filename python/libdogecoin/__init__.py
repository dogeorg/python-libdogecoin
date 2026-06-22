"""libdogecoin — cffi bindings for the libdogecoin C library.

This preserves the historic ``w_*`` wrapper API (so existing tests and
downstream users keep working) while running on cffi instead of Cython. The
bound surface tracks whichever libdogecoin release was fetched: every wrapper
is guarded so that, on an older pin that lacks a function, calling it raises a
clear NotImplementedError instead of failing at import.

Start the secp256k1 context with ``w_context_start()`` before key operations.
"""
from __future__ import annotations

from ._libdogecoin_cffi import ffi, lib  # type: ignore

# v0.1.0-era length assumptions (the historic .pyx used these literals).
_PRIVKEY_WIF_LEN = 53
_MASTER_KEY_LEN = 128
_P2PKH_LEN = 35
_TX_HEX_MAX = 1024 * 100

# BIP39 buffer sizes (from libdogecoin.h defines)
_MNEMONIC_LEN = 1024   # MAX_MNEMONIC_SIZE
_PASS_LEN = 256        # MAX_PASS_SIZE
_SEED_LEN = 64         # MAX_SEED_SIZE (bytes)
_HEX_ENT_LEN = 65     # MAX_HEX_ENT_SIZE

# 0.1.3+ sizes
_PUBKEY_HEX_LEN = 67   # PUBKEYHEXLEN
_PUBKEY_HASH_LEN = 41  # PUBKEYHASHLEN
_PRIVKEY_HEX_LEN = 32  # DOGECOIN_ECKEY_PKEY_LENGTH (raw 32-byte key, hex = 64+1)
_PRIVKEY_HEX_STR_LEN = 65  # 64 hex chars + NUL
_HD_KEY_LEN = 128      # HDKEYLEN (112 in header but library uses 128)
_KEY_PATH_LEN = 256    # KEYPATHMAXLEN
_KOINU_STR_LEN = 32    # enough for uint64 in decimal + decimal point
_BALANCE_STR_LEN = 32


def _has(name: str) -> bool:
    return hasattr(lib, name)


def _require(name: str):
    if not _has(name):
        raise NotImplementedError(
            f"{name} is not present in the libdogecoin release this package was "
            f"built against; rebuild against a newer libdogecoin to use it"
        )
    return getattr(lib, name)


def _b(s):
    if s is None:
        return ffi.NULL
    return s if isinstance(s, bytes) else str(s).encode("utf-8")


def _buf(n: int):
    return ffi.new(f"char[{n}]", b"\x00" * n)


def _s(cbuf) -> str:
    return ffi.string(cbuf).decode("utf-8")


# === CONTEXT =================================================================

def w_context_start() -> None:
    """Start the secp256k1 context. Call before any key/address operation."""
    _require("dogecoin_ecc_start")()


def w_context_stop() -> None:
    """Stop the secp256k1 context."""
    _require("dogecoin_ecc_stop")()


# === ADDRESS =================================================================

def w_generate_priv_pub_key_pair(chain_code: int = 0, as_bytes: bool = False):
    """Generate a WIF private key and matching p2pkh address.

    chain_code: 0 for mainnet, 1 for testnet.
    """
    assert chain_code in (0, 1)
    wif = _buf(_PRIVKEY_WIF_LEN)
    addr = _buf(_P2PKH_LEN)
    _require("generatePrivPubKeypair")(wif, addr, chain_code)
    if as_bytes:
        return ffi.string(wif), ffi.string(addr)
    return _s(wif), _s(addr)


def w_generate_hd_master_pub_key_pair(chain_code: int = 0, as_bytes: bool = False):
    """Generate an HD master private key and matching p2pkh address."""
    assert chain_code in (0, 1)
    master = _buf(_MASTER_KEY_LEN)
    addr = _buf(_P2PKH_LEN)
    _require("generateHDMasterPubKeypair")(master, addr, chain_code)
    if as_bytes:
        return ffi.string(master), ffi.string(addr)
    # historic behavior truncated the testnet address to 34 chars; the address
    # buffer is already NUL-terminated by the lib, so plain decode is correct.
    return _s(master), _s(addr)


def w_generate_derived_hd_pub_key(wif_privkey_master, as_bytes: bool = False):
    """Derive a child p2pkh address from an HD master private key."""
    master = _b(wif_privkey_master)
    out = _buf(_MASTER_KEY_LEN)
    _require("generateDerivedHDPubkey")(master, out)
    return ffi.string(out) if as_bytes else _s(out)


def w_verify_priv_pub_keypair(wif_privkey, p2pkh_pubkey, chain_code: int = 0) -> bool:
    """Verify a WIF private key matches a p2pkh address."""
    assert chain_code in (0, 1)
    return bool(_require("verifyPrivPubKeypair")(_b(wif_privkey), _b(p2pkh_pubkey), chain_code))


def w_verify_master_priv_pub_keypair(wif_privkey_master, p2pkh_pubkey_master,
                                     chain_code: int = 0) -> bool:
    """Verify an HD master key matches a p2pkh address."""
    assert chain_code in (0, 1)
    return bool(_require("verifyHDMasterPubKeypair")(
        _b(wif_privkey_master), _b(p2pkh_pubkey_master), chain_code))


def w_verify_p2pkh_address(p2pkh_pubkey) -> bool:
    """Validate Dogecoin p2pkh address format."""
    raw = _b(p2pkh_pubkey)
    return bool(_require("verifyP2pkhAddress")(raw, len(raw)))


# === TRANSACTION (stateful working-tx table) =================================

def w_start_transaction() -> int:
    """Create a new empty working transaction; returns its index."""
    return int(_require("start_transaction")())


def w_add_utxo(tx_index: int, hex_utxo_txid, vout) -> int:
    """Add an input (utxo) to the working transaction at tx_index."""
    return int(_require("add_utxo")(tx_index, _b(hex_utxo_txid), int(vout)))


def w_add_output(tx_index: int, destination_address, amount) -> int:
    """Add an output to the working transaction at tx_index."""
    return int(_require("add_output")(
        tx_index, _b(destination_address), _b(str(amount))))


def w_finalize_transaction(tx_index: int, destination_address, subtracted_fee,
                           out_dogeamount_for_verification, changeaddress):
    """Finalize the working transaction; returns the raw hex or 0 on failure."""
    res = _require("finalize_transaction")(
        tx_index, _b(destination_address), _b(str(subtracted_fee)),
        _b(str(out_dogeamount_for_verification)), _b(changeaddress))
    if res == ffi.NULL:
        return 0
    return _s(res)


def w_get_raw_transaction(tx_index: int):
    """Return the working transaction at tx_index as raw hex, or 0."""
    res = _require("get_raw_transaction")(tx_index)
    if res == ffi.NULL:
        return 0
    return _s(res)


def w_clear_transaction(tx_index: int) -> None:
    """Discard the working transaction at tx_index."""
    _require("clear_transaction")(tx_index)


def w_sign_raw_transaction(tx_index: int, incoming_raw_tx, script_hex,
                           sig_hash_type: int, privkey):
    """Sign a finalized raw transaction; returns signed hex or 0.

    Mirrors the historic wrapper: a generous fixed buffer holds the (possibly
    extended) signed transaction, which the C function writes in place.
    """
    raw = _b(incoming_raw_tx)
    cbuf = _buf(_TX_HEX_MAX)
    # copy incoming hex into the working buffer (C signs in place)
    ffi.memmove(cbuf, raw, len(raw))
    rc = _require("sign_raw_transaction")(
        tx_index, cbuf, _b(script_hex), sig_hash_type, _b(privkey))
    if rc:
        return _s(cbuf)
    return 0


def w_sign_transaction(tx_index: int, script_pubkey, privkey) -> int:
    """Sign all inputs of the working transaction at tx_index."""
    return int(_require("sign_transaction")(tx_index, _b(script_pubkey), _b(privkey)))


def w_store_raw_transaction(incoming_raw_tx) -> int:
    """Store an already-formed raw transaction; returns its index."""
    return int(_require("store_raw_transaction")(_b(incoming_raw_tx)))


def w_remove_all() -> None:
    """Clear all internal working transactions."""
    _require("remove_all")()


# === HD ADDRESSES (0.1.2+) ==================================================

def w_get_derived_hd_address(masterkey, account: int, ischange: int,
                              addressindex: int, outprivkey: bool = False):
    """Derive a HD address (or privkey) by account/change/index path."""
    out = _buf(_MASTER_KEY_LEN)
    rc = _require("getDerivedHDAddress")(
        _b(masterkey), account, ischange, addressindex, out, int(outprivkey))
    if not rc:
        return None
    return _s(out)


def w_get_derived_hd_address_by_path(masterkey, derived_path,
                                      outprivkey: bool = False):
    """Derive a HD address (or privkey) by an explicit BIP32 derivation path."""
    out = _buf(_MASTER_KEY_LEN)
    rc = _require("getDerivedHDAddressByPath")(
        _b(masterkey), _b(derived_path), out, int(outprivkey))
    if not rc:
        return None
    return _s(out)


# === BIP39 MNEMONIC (0.1.2+) ================================================

def w_generate_english_mnemonic(entropy, size):
    """Generate an English mnemonic from hex entropy.

    entropy: hex string (e.g. 32 hex chars for 128-bit entropy)
    size: entropy bit length as string — "128", "160", "192", "224", or "256"
    Returns: mnemonic phrase string, or None on failure.
    """
    mnemonic = _buf(_MNEMONIC_LEN)
    rc = _require("generateEnglishMnemonic")(_b(entropy), _b(size), mnemonic)
    if rc < 0:
        return None
    return _s(mnemonic)


def w_generate_random_english_mnemonic(size):
    """Generate a random English mnemonic phrase.

    size: entropy bit length as string — "128", "160", "192", "224", or "256"
    Returns: mnemonic phrase string, or None on failure.
    """
    mnemonic = _buf(_MNEMONIC_LEN)
    rc = _require("generateRandomEnglishMnemonic")(_b(size), mnemonic)
    if rc < 0:
        return None
    return _s(mnemonic)


def w_dogecoin_seed_from_mnemonic(mnemonic, passphrase: str = "") -> bytes | None:
    """Derive a 64-byte BIP32 seed from a mnemonic phrase and optional passphrase.

    Returns: raw bytes (64 bytes), or None on failure.
    """
    seed = ffi.new("uint8_t[64]")
    rc = _require("dogecoin_seed_from_mnemonic")(_b(mnemonic), _b(passphrase), seed)
    if rc < 0:
        return None
    return bytes(ffi.buffer(seed, _SEED_LEN))


def w_get_derived_hd_address_from_mnemonic(account: int, index: int,
                                            change_level,
                                            mnemonic, passphrase: str = "",
                                            chain_code: int = 0):
    """Derive a p2pkh address directly from a BIP39 mnemonic.

    account: BIP44 account number
    index: address index
    change_level: "0" for external chain, "1" for internal/change
    mnemonic: BIP39 mnemonic phrase
    passphrase: optional BIP39 passphrase
    chain_code: 0 for mainnet, 1 for testnet
    Returns: p2pkh address string, or None on failure.
    """
    addr = _buf(_P2PKH_LEN + 4)
    rc = _require("getDerivedHDAddressFromMnemonic")(
        account, index, _b(change_level), _b(mnemonic), _b(passphrase),
        addr, chain_code)
    if rc < 0:
        return None
    return _s(addr)


# === QR CODE (0.1.2+) =======================================================

def w_qrgen_p2pkh_to_qr_string(p2pkh) -> str | None:
    """Return a text-art QR code string for a p2pkh address (with line breaks)."""
    out = _buf(32768)
    rc = _require("qrgen_p2pkh_to_qr_string")(_b(p2pkh), out)
    if not rc:
        return None
    return _s(out)


def w_qrgen_p2pkh_consoleprint_to_qr(p2pkh) -> None:
    """Print a QR code for a p2pkh address directly to stdout."""
    _require("qrgen_p2pkh_consoleprint_to_qr")(_b(p2pkh))


def w_qrgen_string_to_qr_pngfile(filename, data, size_multiplier: int = 4) -> int:
    """Write a QR code as a PNG file.

    filename: output filename (including .png extension)
    data: string to encode in the QR code
    size_multiplier: pixel size multiplier (default 4)
    Returns: 1 on success, 0 on failure.
    """
    return int(_require("qrgen_string_to_qr_pngfile")(
        _b(filename), _b(data), size_multiplier))


def w_qrgen_string_to_qr_jpgfile(filename, data, size_multiplier: int = 4) -> int:
    """Write a QR code as a JPEG file.

    filename: output filename (including .jpg extension)
    data: string to encode in the QR code
    size_multiplier: pixel size multiplier (default 4)
    Returns: 1 on success, 0 on failure.
    """
    return int(_require("qrgen_string_to_qr_jpgfile")(
        _b(filename), _b(data), size_multiplier))


# === MESSAGE SIGNING (0.1.2+) ===============================================

def w_sign_message(privkey, message) -> str | None:
    """Sign an arbitrary message with a WIF private key.

    Returns: base64-encoded signature string, or None on failure.
    """
    res = _require("sign_message")(_b(privkey), _b(message))
    if res == ffi.NULL:
        return None
    return ffi.string(res).decode("utf-8")


def w_verify_message(signature, message, address) -> bool:
    """Verify a signed message against a p2pkh address.

    signature: base64-encoded signature (from w_sign_message)
    message: the original message string
    address: the p2pkh address corresponding to the signing key
    Returns: True if the signature is valid, False otherwise.
    """
    return bool(_require("verify_message")(_b(signature), _b(message), _b(address)))


# === ADDRESS / PUBKEY UTILITIES (0.1.3+) =====================================

def w_is_testnet_from_b58prefix(address) -> bool:
    """Return True if the address has a testnet base58 prefix."""
    return bool(_require("isTestnetFromB58Prefix")(_b(address)))


def w_is_mainnet_from_b58prefix(address) -> bool:
    """Return True if the address has a mainnet base58 prefix."""
    return bool(_require("isMainnetFromB58Prefix")(_b(address)))


def w_get_address_from_pubkey(pubkey_hex, is_testnet: bool = False):
    """Derive a p2pkh address from a compressed public key (hex).

    Returns: p2pkh address string, or None on failure.
    """
    out = _buf(_P2PKH_LEN + 4)
    rc = _require("getAddressFromPubkey")(_b(pubkey_hex), int(is_testnet), out)
    return _s(out) if rc else None


def w_get_pubkey_from_privkey(privkey_wif, is_testnet: bool = False):
    """Derive the compressed public key (hex) from a WIF private key.

    Returns: pubkey hex string, or None on failure.
    """
    out = _buf(_PUBKEY_HEX_LEN)
    sz = ffi.new("size_t[1]", [_PUBKEY_HEX_LEN])
    rc = _require("getPubkeyFromPrivkey")(_b(privkey_wif), int(is_testnet), out, sz)
    return _s(out) if rc else None


def w_gen_privkey(is_testnet: bool = False):
    """Generate a new private key.

    Returns: (wif_privkey, privkey_hex) tuple, or None on failure.
    """
    wif = _buf(_PRIVKEY_WIF_LEN)
    hex_key = _buf(_PRIVKEY_HEX_STR_LEN)
    rc = _require("genPrivkey")(int(is_testnet), wif, _PRIVKEY_WIF_LEN, hex_key)
    return (_s(wif), _s(hex_key)) if rc else None


def w_dogecoin_address_to_pubkey_hash(p2pkh) -> str | None:
    """Convert a p2pkh address to its pubkey hash hex string (lib-allocated).

    Returns: pubkey hash hex string, or None on failure.
    """
    res = _require("dogecoin_address_to_pubkey_hash")(_b(p2pkh))
    if res == ffi.NULL:
        return None
    return ffi.string(res).decode("utf-8")


def w_dogecoin_private_key_wif_to_pubkey_hash(privkey_wif) -> str | None:
    """Derive the pubkey hash hex string from a WIF private key (lib-allocated).

    Returns: pubkey hash hex string, or None on failure.
    """
    res = _require("dogecoin_private_key_wif_to_pubkey_hash")(_b(privkey_wif))
    if res == ffi.NULL:
        return None
    return ffi.string(res).decode("utf-8")


def w_dogecoin_p2pkh_address_to_pubkey_hash(p2pkh):
    """Convert a p2pkh address to its pubkey hash (scripthash) hex string.

    Returns: pubkey hash hex string, or None on failure.
    """
    out = _buf(_PUBKEY_HASH_LEN)
    rc = _require("dogecoin_p2pkh_address_to_pubkey_hash")(_b(p2pkh), out)
    return _s(out) if rc else None


def w_get_addr_from_pubkey_hash(pubkey_hash, is_testnet: bool = False):
    """Convert a pubkey hash hex string to a p2pkh address.

    Returns: p2pkh address string, or None on failure.
    """
    out = _buf(_P2PKH_LEN + 4)
    rc = _require("getAddrFromPubkeyHash")(_b(pubkey_hash), int(is_testnet), out)
    return _s(out) if rc else None


def w_get_wif_encoded_privkey(privkey_hex, is_testnet: bool = False):
    """WIF-encode a raw 32-byte private key (given as 64-char hex string).

    Returns: WIF-encoded private key string.
    """
    out = _buf(_PRIVKEY_WIF_LEN)
    sz = ffi.new("size_t[1]", [_PRIVKEY_WIF_LEN])
    _require("getWifEncodedPrivKey")(_b(privkey_hex), int(is_testnet), out, sz)
    return _s(out)


def w_get_decoded_privkey_wif(privkey_wif, is_testnet: bool = False):
    """Decode a WIF-encoded private key to its 32-byte hex representation.

    Returns: privkey hex string, or None on failure.
    """
    out = _buf(_PRIVKEY_HEX_STR_LEN)
    rc = _require("getDecodedPrivKeyWif")(_b(privkey_wif), int(is_testnet), out)
    return _s(out) if rc else None


# === HD KEY UTILITIES (0.1.3+) ===============================================

def w_get_hd_root_key_from_seed(seed_bytes: bytes, is_testnet: bool = False):
    """Derive an HD master key from a 64-byte BIP32 seed.

    seed_bytes: 64 bytes (e.g. from w_dogecoin_seed_from_mnemonic)
    Returns: HD master key string (xprv), or None on failure.
    """
    seed_buf = ffi.new("uint8_t[]", seed_bytes)
    out = _buf(_HD_KEY_LEN)
    rc = _require("getHDRootKeyFromSeed")(seed_buf, len(seed_bytes), int(is_testnet), out)
    return _s(out) if rc else None


def w_get_hd_pub_key(hdkey, is_testnet: bool = False):
    """Extract the extended public key (xpub) from an extended private key.

    Returns: xpub string, or None on failure.
    """
    out = _buf(_HD_KEY_LEN)
    rc = _require("getHDPubKey")(_b(hdkey), int(is_testnet), out)
    return _s(out) if rc else None


def w_derive_ext_key_from_hd_key(extkey, keypath, is_testnet: bool = False):
    """Derive an extended private key from another extended key by path.

    Returns: derived extended key string, or None on failure.
    """
    out = _buf(_HD_KEY_LEN)
    rc = _require("deriveExtKeyFromHDKey")(
        _b(extkey), _b(keypath), int(is_testnet), out)
    return _s(out) if rc else None


def w_derive_ext_pub_key_from_hd_key(extpubkey, keypath, is_testnet: bool = False):
    """Derive an extended public key from an extended public key by path.

    Returns: derived extended public key string, or None on failure.
    """
    out = _buf(_HD_KEY_LEN)
    rc = _require("deriveExtPubKeyFromHDKey")(
        _b(extpubkey), _b(keypath), int(is_testnet), out)
    return _s(out) if rc else None


def w_gen_hd_master(is_testnet: bool = False):
    """Generate a new random HD master private key.

    Returns: HD master key string (xprv), or None on failure.
    """
    out = _buf(_HD_KEY_LEN)
    rc = _require("genHDMaster")(int(is_testnet), out, _HD_KEY_LEN)
    return _s(out) if rc else None


def w_derive_hd_ext_from_master(masterkey, keypath, is_testnet: bool = False):
    """Derive an extended key from a master key by explicit path.

    Returns: derived extended key string, or None on failure.
    """
    out = _buf(_HD_KEY_LEN)
    rc = _require("deriveHDExtFromMaster")(
        int(is_testnet), _b(masterkey), _b(keypath), out, _HD_KEY_LEN)
    return _s(out) if rc else None


def w_get_hd_node_privkey_wif_by_path(masterkey, derived_path,
                                       outprivkey: bool = False) -> str | None:
    """Derive a WIF private key (or p2pkh address) from an HD master key by path.

    outprivkey=False returns the p2pkh address at that path.
    outprivkey=True returns the WIF private key at that path.
    Returns: string result (lib-allocated), or None on failure.
    """
    addr_buf = _buf(_P2PKH_LEN + 4)
    res = _require("getHDNodePrivateKeyWIFByPath")(
        _b(masterkey), _b(derived_path), addr_buf, int(outprivkey))
    if res == ffi.NULL:
        return None
    return ffi.string(res).decode("utf-8")


def w_derive_bip44_extended_key(masterkey, account: int | None,
                                 change_level,
                                 address_index: int | None,
                                 path=None,
                                 is_testnet: bool = False):
    """Derive a BIP44 extended private key.

    account: BIP44 account number, or None to omit (uses library default)
    change_level: "0" for external chain, "1" for internal/change
    address_index: address index, or None to omit
    path: explicit key path override string, or None
    Returns: (extended_key, keypath) tuple, or None on failure.
    """
    acct_p = ffi.NULL if account is None else ffi.new("uint32_t[1]", [account])
    idx_p = ffi.NULL if address_index is None else ffi.new("uint32_t[1]", [address_index])
    extkeyout = _buf(_HD_KEY_LEN)
    keypathout = _buf(_KEY_PATH_LEN)
    rc = _require("deriveBIP44ExtendedKey")(
        _b(masterkey), acct_p, _b(str(change_level)), idx_p,
        _b(path) if path else ffi.NULL, extkeyout, keypathout)
    return (_s(extkeyout), _s(keypathout)) if rc else None


def w_derive_bip44_extended_public_key(masterkey, account: int | None,
                                        change_level,
                                        address_index: int | None,
                                        path=None,
                                        is_testnet: bool = False):
    """Derive a BIP44 extended public key.

    account: BIP44 account number, or None to omit
    change_level: "0" for external chain, "1" for internal/change
    address_index: address index, or None to omit
    path: explicit key path override string, or None
    Returns: (extended_pubkey, keypath) tuple, or None on failure.
    """
    acct_p = ffi.NULL if account is None else ffi.new("uint32_t[1]", [account])
    idx_p = ffi.NULL if address_index is None else ffi.new("uint32_t[1]", [address_index])
    extkeyout = _buf(_HD_KEY_LEN)
    keypathout = _buf(_KEY_PATH_LEN)
    rc = _require("deriveBIP44ExtendedPublicKey")(
        _b(masterkey), acct_p, _b(str(change_level)), idx_p,
        _b(path) if path else ffi.NULL, extkeyout, keypathout)
    return (_s(extkeyout), _s(keypathout)) if rc else None


# === KOINU UTILITIES (0.1.3+) ================================================

def w_koinu_to_coins_str(koinu: int) -> str | None:
    """Convert a koinu (integer, 1 DOGE = 100000000 koinu) to a decimal coin string.

    Returns: decimal string (e.g. "1.00000000"), or None on failure.
    """
    out = _buf(_KOINU_STR_LEN)
    rc = _require("koinu_to_coins_str")(koinu, out)
    return _s(out) if rc else None


def w_coins_to_koinu_str(coins) -> int:
    """Convert a decimal coin string (e.g. "1.5") to koinu (integer).

    Returns: koinu value as int (1 DOGE = 100000000).
    """
    return int(_require("coins_to_koinu_str")(_b(str(coins))))


# === TRANSACTION — new 0.1.3 variant =========================================

def w_sign_transaction_w_privkey(tx_index: int, vout_index: int, privkey) -> int:
    """Sign a specific input of the working transaction by vout index.

    Returns: 1 on success, 0 on failure.
    """
    return int(_require("sign_transaction_w_privkey")(tx_index, vout_index, _b(privkey)))


# === WALLET / SPV ============================================================
# The SPV watch/balance/utxo functions were exposed prematurely in 0.1.3:
# they query a libdogecoin SPV node (dogecoin_spv_client) that this binding
# provides no way to create, configure, or run, and the register half of the
# register/unregister pair was never bound. As shipped they could not function.
# They are withdrawn here pending a complete SPV binding (node lifecycle
# new/free/load/discover_peers + a non-blocking runloop, register +
# unregister, balance/utxo queries) which will land as a single coherent
# feature rather than a partial surface. See 0.2.0 SPV work.


# === SURFACE INTROSPECTION ===================================================

def available() -> list[str]:
    """Names of libdogecoin C functions present in the build this wheel links."""
    import json
    from importlib.resources import files
    try:
        data = json.loads((files(__package__) / "_surface.json").read_text())
        return [f["name"] for f in data["functions"]]
    except Exception:
        # fall back to probing the lib object
        return [n for n in dir(lib) if not n.startswith("_")]


# === TIER 3: object-oriented handle API ======================================
# HD node / chain params are bound only when the linked libdogecoin exposes the
# dogecoin_hdnode_* surface. Import is guarded so a build without it still loads
# the Tier 1 w_* API cleanly; HDNode is simply absent.
try:
    from ._hdnode import HDNode, ChainParams, MAINNET, TESTNET, REGTEST  # noqa: F401
    from ._handle import HandleError, UseAfterFreeError  # noqa: F401
    _HAS_TIER3 = True
except (ImportError, AttributeError):
    _HAS_TIER3 = False
