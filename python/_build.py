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
import platform
import shutil
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


def _find_libunistring() -> str | None:
    """Locate libunistring.a — pkg-config first, then multiarch fallback."""
    if shutil.which("pkg-config"):
        try:
            libdir = subprocess.check_output(
                ["pkg-config", "--variable=libdir", "libunistring"],
                stderr=subprocess.DEVNULL, text=True).strip()
            if libdir:
                p = Path(libdir) / "libunistring.a"
                if p.exists():
                    return str(p)
        except subprocess.CalledProcessError:
            pass
    arch_map = {
        "x86_64": "x86_64-linux-gnu",
        "aarch64": "aarch64-linux-gnu",
        "armv7l": "arm-linux-gnueabihf",
        "i686": "i386-linux-gnu",
    }
    multiarch = arch_map.get(platform.machine(), "")
    for d in [f"/usr/lib/{multiarch}", "/usr/lib", "/usr/local/lib"]:
        p = Path(d) / "libunistring.a"
        if p.exists():
            return str(p)
    return None


def _extra_objects() -> list[str]:
    objs = [str(LIBA)]
    if LIBA.exists() and _needs_unistring(LIBA):
        u = _find_libunistring()
        if u:
            objs.append(u)
    return objs


ffibuilder = FFI()
ffibuilder.cdef(_ensure_cdef())
ffibuilder.set_source(
    "libdogecoin._libdogecoin_cffi",
    '#include "libdogecoin.h"',
    include_dirs=[str(ROOT / "include")],
    extra_objects=_extra_objects(),
    # Build against the CPython stable ABI so a single wheel per platform
    # serves CPython 3.10+ instead of one wheel per interpreter minor.
    py_limited_api=True,
)

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
