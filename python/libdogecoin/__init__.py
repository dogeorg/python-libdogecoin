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
