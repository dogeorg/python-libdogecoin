"""EC private key / public key objects (Layer B).

Wraps libdogecoin's `dogecoin_key` and `dogecoin_pubkey`. Unlike the HD node
(a heap object from `_new()`/`_free()`), these structs are caller-allocated:
the C API initializes a struct you own. So the cffi struct is allocated here and
its lifetime is cffi's; "release" means **cleanse** — zeroing the secret bytes —
not freeing memory.

Security: a Key cleanses its private-key bytes on explicit free(), on context-
manager exit, and as a GC backstop. Prefer `with`:

    from libdogecoin import Key, PubKey, MAINNET

    with Key.generate() as k:
        wif = k.to_wif(MAINNET)
        pub = k.pubkey()
        sig = k.sign(hash32)
        assert pub.verify(hash32, sig)
    # k's private bytes are wiped here

The private bytes are still in `k`'s freed struct only until cffi reclaims it;
cleanse zeroes them at scope exit so they do not linger in the meantime.
"""
from __future__ import annotations

from ._libdogecoin_cffi import ffi, lib  # type: ignore
from ._handle import _Handle, HandleError
from ._hdnode import ChainParams

_PRIVKEY_LEN = 32
_PUBKEY_COMPRESSED_LEN = 33
_PUBKEY_UNCOMPRESSED_LEN = 65
_HASH_LEN = 32
_SIG_MAX = 74          # DER sig upper bound
_WIF_BUF = 128
_PUBHEX_BUF = 128


class Key(_Handle):
    """An EC private key (libdogecoin dogecoin_key). Cleansed on release."""

    def __init__(self, ptr) -> None:
        # release = cleanse the secret bytes (NOT a heap free; cffi owns the
        # struct memory and reclaims it when this object is collected).
        super().__init__(ptr, lib.dogecoin_privkey_cleanse)

    @classmethod
    def _alloc(cls) -> "Key":
        ptr = ffi.new("dogecoin_key*")
        lib.dogecoin_privkey_init(ptr)
        return cls(ptr)

    @classmethod
    def generate(cls) -> "Key":
        """Generate a new random private key."""
        k = cls._alloc()
        if not lib.dogecoin_privkey_gen(k._ptr):
            k.free()
            raise HandleError("dogecoin_privkey_gen failed")
        return k

    @classmethod
    def from_wif(cls, wif: str, chain: ChainParams) -> "Key":
        """Decode a WIF string into a private key (bridge from Tier 1)."""
        k = cls._alloc()
        ok = lib.dogecoin_privkey_decode_wif(
            wif.encode("utf-8"), chain._ptr, k._ptr)
        if not ok:
            k.free()
            raise HandleError("dogecoin_privkey_decode_wif failed")
        return k

    def is_valid(self) -> bool:
        return bool(lib.dogecoin_privkey_is_valid(self._ptr))

    def to_wif(self, chain: ChainParams) -> str:
        """WIF-encode this key (bridge to the Tier 1 string world)."""
        buf = ffi.new(f"char[{_WIF_BUF}]")
        size = ffi.new("size_t*", _WIF_BUF)
        lib.dogecoin_privkey_encode_wif(self._ptr, chain._ptr, buf, size)
        return ffi.string(buf).decode("utf-8")

    def pubkey(self) -> "PubKey":
        """Derive the corresponding public key."""
        pub = PubKey._alloc()
        lib.dogecoin_pubkey_from_key(self._ptr, pub._ptr)
        return pub

    def sign(self, hash32: bytes) -> bytes:
        """Sign a 32-byte hash, returning a DER-encoded signature."""
        if len(hash32) != _HASH_LEN:
            raise ValueError(f"hash must be {_HASH_LEN} bytes, got {len(hash32)}")
        sig = ffi.new(f"unsigned char[{_SIG_MAX}]")
        outlen = ffi.new("size_t*", _SIG_MAX)
        if not lib.dogecoin_key_sign_hash(self._ptr, hash32, sig, outlen):
            raise HandleError("dogecoin_key_sign_hash failed")
        return bytes(ffi.buffer(sig, outlen[0]))

    @property
    def private_bytes(self) -> bytes:
        """The raw 32-byte private key. Handle with care."""
        return bytes(ffi.buffer(self._ptr.privkey, _PRIVKEY_LEN))

    def __repr__(self) -> str:
        return "<Key (cleansed)>" if self.closed else "<Key (private)>"


class PubKey(_Handle):
    """An EC public key (libdogecoin dogecoin_pubkey)."""

    def __init__(self, ptr) -> None:
        super().__init__(ptr, lib.dogecoin_pubkey_cleanse)

    @classmethod
    def _alloc(cls) -> "PubKey":
        ptr = ffi.new("dogecoin_pubkey*")
        lib.dogecoin_pubkey_init(ptr)
        return cls(ptr)

    def is_valid(self) -> bool:
        return bool(lib.dogecoin_pubkey_is_valid(self._ptr))

    def hex(self) -> str:
        buf = ffi.new(f"char[{_PUBHEX_BUF}]")
        size = ffi.new("size_t*", _PUBHEX_BUF)
        if not lib.dogecoin_pubkey_get_hex(self._ptr, buf, size):
            raise HandleError("dogecoin_pubkey_get_hex failed")
        return ffi.string(buf).decode("utf-8")

    def hash160(self) -> bytes:
        out = ffi.new("uint8_t[20]")
        lib.dogecoin_pubkey_get_hash160(self._ptr, out)
        return bytes(ffi.buffer(out, 20))

    def verify(self, hash32: bytes, sig_der: bytes) -> bool:
        """Verify a DER signature over a 32-byte hash."""
        if len(hash32) != _HASH_LEN:
            raise ValueError(f"hash must be {_HASH_LEN} bytes, got {len(hash32)}")
        sigbuf = ffi.new(f"unsigned char[{len(sig_der)}]", sig_der)
        return bool(lib.dogecoin_pubkey_verify_sig(
            self._ptr, hash32, sigbuf, len(sig_der)))

    @property
    def compressed(self) -> bool:
        return bool(self._ptr.compressed)

    @property
    def raw(self) -> bytes:
        n = _PUBKEY_COMPRESSED_LEN if self.compressed else _PUBKEY_UNCOMPRESSED_LEN
        return bytes(ffi.buffer(self._ptr.pubkey, n))

    def __repr__(self) -> str:
        if self.closed:
            return "<PubKey (cleansed)>"
        return f"<PubKey {self.hex()[:16]}...>"
