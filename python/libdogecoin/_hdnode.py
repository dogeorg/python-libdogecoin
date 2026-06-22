"""HD (BIP32) node — the first Tier 3 object binding.

Wraps a libdogecoin `dogecoin_hdnode` C struct as a Python object with managed
lifetime (see _handle._Handle). Where the flat Tier 1 `w_*` functions take and
return strings, this exposes the node as a live object you derive children from,
read fields off, and serialize:

    from libdogecoin import HDNode, MAINNET

    seed = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
    with HDNode.from_seed(seed) as master:
        child = master.derive_private(0)           # m/0
        print(child.serialize_private(MAINNET))    # dgpv...
        print(child.public_key.hex())              # field read straight off the struct

Derivation mutates in place in libdogecoin; this wrapper copies first so each
derive_* returns a new, independently-owned node and never mutates the receiver.
"""
from __future__ import annotations

from ._libdogecoin_cffi import ffi, lib  # type: ignore
from ._handle import _Handle, HandleError

# hdnode serialization buffer: header notes HDKEYLEN is 112 but the function
# historically expects up to 128; allocate generously.
_HD_SERIALIZE_LEN = 128
_CHAINCODE_LEN = 32
_PRIVKEY_LEN = 32
_PUBKEY_COMPRESSED_LEN = 33


class ChainParams:
    """A libdogecoin chain parameter set (mainnet / testnet / regtest).

    Thin wrapper over the `extern const dogecoin_chainparams` globals. These are
    static C objects owned by the library, so this is NOT a _Handle — there is
    nothing to free.
    """

    __slots__ = ("_cptr", "name")

    def __init__(self, cptr, name: str) -> None:
        self._cptr = cptr
        self.name = name

    @property
    def _ptr(self):
        return self._cptr

    def __repr__(self) -> str:
        return f"<ChainParams {self.name}>"


# the three library-owned global chain parameter sets, via cffi accessors
MAINNET = ChainParams(lib.dogecoin_chainparams_main_ptr(), "mainnet")
TESTNET = ChainParams(lib.dogecoin_chainparams_test_ptr(), "testnet")
REGTEST = ChainParams(lib.dogecoin_chainparams_regtest_ptr(), "regtest")


class HDNode(_Handle):
    """A BIP32 hierarchical-deterministic node (libdogecoin dogecoin_hdnode)."""

    def __init__(self, ptr) -> None:
        super().__init__(ptr, lib.dogecoin_hdnode_free)

    # --- construction --------------------------------------------------------

    @classmethod
    def new(cls) -> "HDNode":
        """Allocate a new, empty HD node."""
        ptr = lib.dogecoin_hdnode_new()
        if ptr == ffi.NULL:
            raise HandleError("dogecoin_hdnode_new returned NULL")
        return cls(ptr)

    @classmethod
    def from_seed(cls, seed: bytes) -> "HDNode":
        """Build a master HD node from a BIP32 seed (typically 64 bytes)."""
        node = cls.new()
        ok = lib.dogecoin_hdnode_from_seed(seed, len(seed), node._ptr)
        if not ok:
            node.free()
            raise HandleError("dogecoin_hdnode_from_seed failed")
        return node

    def copy(self) -> "HDNode":
        """Return an independently-owned copy of this node."""
        ptr = lib.dogecoin_hdnode_copy(self._ptr)
        if ptr == ffi.NULL:
            raise HandleError("dogecoin_hdnode_copy returned NULL")
        return HDNode(ptr)

    # --- derivation (copy-then-mutate so the receiver is never changed) ------

    def derive_private(self, index: int) -> "HDNode":
        """Derive the child private node at `index` (CKD private)."""
        child = self.copy()
        if not lib.dogecoin_hdnode_private_ckd(child._ptr, index):
            child.free()
            raise HandleError(f"private CKD failed at index {index}")
        return child

    def derive_public(self, index: int) -> "HDNode":
        """Derive the child public node at `index` (CKD public)."""
        child = self.copy()
        if not lib.dogecoin_hdnode_public_ckd(child._ptr, index):
            child.free()
            raise HandleError(f"public CKD failed at index {index}")
        return child

    def fill_public_key(self) -> None:
        """(Re)compute the public key from the private key, in place."""
        lib.dogecoin_hdnode_fill_public_key(self._ptr)

    # --- serialization -------------------------------------------------------

    def serialize_public(self, chain: ChainParams) -> str:
        buf = ffi.new(f"char[{_HD_SERIALIZE_LEN}]")
        lib.dogecoin_hdnode_serialize_public(self._ptr, chain._ptr, buf,
                                             _HD_SERIALIZE_LEN)
        return ffi.string(buf).decode("utf-8")

    def serialize_private(self, chain: ChainParams) -> str:
        buf = ffi.new(f"char[{_HD_SERIALIZE_LEN}]")
        lib.dogecoin_hdnode_serialize_private(self._ptr, chain._ptr, buf,
                                              _HD_SERIALIZE_LEN)
        return ffi.string(buf).decode("utf-8")

    @classmethod
    def deserialize(cls, extkey: str, chain: ChainParams) -> "HDNode":
        """Parse an extended key string (dgpv.../dgub...) into a node."""
        node = cls.new()
        ok = lib.dogecoin_hdnode_deserialize(
            extkey.encode("utf-8"), chain._ptr, node._ptr)
        if not ok:
            node.free()
            raise HandleError("dogecoin_hdnode_deserialize failed")
        return node

    def pub_hex(self) -> str:
        """Return the compressed public key as a hex string."""
        # get_pub_hex takes a size_t* in/out; seed it with the buffer size.
        size = ffi.new("size_t*", 128)
        buf = ffi.new("char[128]")
        if not lib.dogecoin_hdnode_get_pub_hex(self._ptr, buf, size):
            raise HandleError("dogecoin_hdnode_get_pub_hex failed")
        return ffi.string(buf).decode("utf-8")

    # --- struct field reads (ergonomics the flat API never had) --------------

    @property
    def depth(self) -> int:
        return int(self._ptr.depth)

    @property
    def fingerprint(self) -> int:
        return int(self._ptr.fingerprint)

    @property
    def child_num(self) -> int:
        return int(self._ptr.child_num)

    @property
    def chain_code(self) -> bytes:
        return bytes(ffi.buffer(self._ptr.chain_code, _CHAINCODE_LEN))

    @property
    def private_key(self) -> bytes:
        return bytes(ffi.buffer(self._ptr.private_key, _PRIVKEY_LEN))

    @property
    def public_key(self) -> bytes:
        return bytes(ffi.buffer(self._ptr.public_key, _PUBKEY_COMPRESSED_LEN))

    def __repr__(self) -> str:
        if self.closed:
            return "<HDNode (freed)>"
        return (f"<HDNode depth={self.depth} child_num={self.child_num} "
                f"pub={self.public_key.hex()[:16]}...>")
