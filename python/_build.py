#!/usr/bin/env python3
"""cffi out-of-line builder for python-libdogecoin.

Drops into the existing dogeorg pipeline: fetch.py populates ./lib/libdogecoin.a
and ./include/libdogecoin.h, then this compiles a cffi extension linking that
static archive. The cdef is generated from the *fetched* header by
codegen/gen_cdef.py, so the bound surface tracks whichever libdogecoin release
was fetched.

The build regenerates the cdef if the codegen + header are present (in-tree /
CI), else falls back to the committed python/_cdef.h (sdist consumers).
"""
import subprocess
import sys
from pathlib import Path

from cffi import FFI

ROOT = Path(__file__).resolve().parent.parent
HEADER = ROOT / "include" / "libdogecoin.h"
LIBA = ROOT / "lib" / "libdogecoin.a"
CDEF = ROOT / "python" / "libdogecoin" / "_cdef.h"
MANIFEST = ROOT / "python" / "libdogecoin" / "_surface.json"
CODEGEN = ROOT / "codegen" / "gen_cdef.py"


def _ensure_cdef() -> str:
    if CODEGEN.exists() and HEADER.exists():
        subprocess.run(
            [sys.executable, str(CODEGEN),
             "--header", str(HEADER),
             "--out-cdef", str(CDEF),
             "--out-manifest", str(MANIFEST)],
            check=True,
        )
    if not CDEF.exists():
        raise RuntimeError(
            "no cdef: need codegen+header (in-tree) or committed python/_cdef.h"
        )
    return CDEF.read_text()


def _needs_unistring(liba: Path) -> bool:
    """Return True if libdogecoin.a has an unresolved ref to uninorm_nfkd."""
    try:
        out = subprocess.check_output(
            ["nm", "-u", str(liba)], stderr=subprocess.DEVNULL, text=True)
        return "uninorm_nfkd" in out
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def _libraries() -> list[str]:
    # Linux dlopen uses RTLD_NOW: all symbols must resolve at load time.
    # Provide libunistring.so dynamically; auditwheel vendors it into the wheel.
    # macOS dyld lazy-binds, so uninorm_nfkd being undefined in the pre-built
    # libdogecoin.a is harmless — don't add unistring there.
    if sys.platform != "linux":
        return []
    if LIBA.exists() and _needs_unistring(LIBA):
        return ["unistring"]
    return []


ffibuilder = FFI()
ffibuilder.cdef(_ensure_cdef())
ffibuilder.set_source(
    "libdogecoin._libdogecoin_cffi",
    '''#include "libdogecoin.h"

/* Tier 3: expose the read-only chain parameter globals as opaque pointers.
   cffi cannot bind an `extern const struct` global directly, so these thin
   accessors hand back a void* the Python side passes through unchanged. */
void* dogecoin_chainparams_main_ptr(void)    { return (void*)&dogecoin_chainparams_main; }
void* dogecoin_chainparams_test_ptr(void)    { return (void*)&dogecoin_chainparams_test; }
void* dogecoin_chainparams_regtest_ptr(void) { return (void*)&dogecoin_chainparams_regtest; }

/* Layer B: EC key/pubkey functions present in libdogecoin.a but not declared
   in libdogecoin.h.  Forward-declare so clang (which errors on implicit
   function declarations) can compile the cffi-generated C source. */
void dogecoin_privkey_init(dogecoin_key* privkey);
int  dogecoin_privkey_is_valid(const dogecoin_key* privkey);
void dogecoin_privkey_cleanse(dogecoin_key* privkey);
int  dogecoin_privkey_gen(dogecoin_key* privkey);
int  dogecoin_privkey_verify_pubkey(dogecoin_key* privkey, dogecoin_pubkey* pubkey);
void dogecoin_pubkey_init(dogecoin_pubkey* pubkey);
int  dogecoin_pubkey_is_valid(const dogecoin_pubkey* pubkey);
void dogecoin_pubkey_cleanse(dogecoin_pubkey* pubkey);
void dogecoin_pubkey_from_key(const dogecoin_key* privkey, dogecoin_pubkey* pubkey_inout);
void dogecoin_pubkey_get_hash160(const dogecoin_pubkey* pubkey, uint8_t* hash160);
int  dogecoin_pubkey_get_hex(const dogecoin_pubkey* pubkey, char* str, size_t* strsize);
int  dogecoin_key_sign_hash(const dogecoin_key* privkey, const uint8_t* hash,
                            unsigned char* sigout, size_t* outlen);
int  dogecoin_pubkey_verify_sig(const dogecoin_pubkey* pubkey, const uint8_t* hash,
                                unsigned char* sigder, size_t len);
''',
    include_dirs=[str(ROOT / "include")],
    extra_objects=[str(LIBA)],
    libraries=_libraries(),
    # Build against the CPython stable ABI so a single wheel per platform
    # serves CPython 3.10+ instead of one wheel per interpreter minor.
    py_limited_api=True,
)

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
