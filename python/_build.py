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


ffibuilder = FFI()
ffibuilder.cdef(_ensure_cdef())
ffibuilder.set_source(
    "libdogecoin._libdogecoin_cffi",
    '#include "libdogecoin.h"',
    include_dirs=[str(ROOT / "include")],
    extra_objects=[str(LIBA)],
    # Build against the CPython stable ABI so a single wheel per platform
    # serves CPython 3.10+ instead of one wheel per interpreter minor.
    py_limited_api=True,
)

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
