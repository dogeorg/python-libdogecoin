#!/usr/bin/python3
"""fetch.py — download (or build) libdogecoin for a given host and tag.

Binary releases: archives are fetched from GitHub and verified against the
signed SHA256SUMS.asc that accompanies each release.

Source-only releases: the source tarball is downloaded, built with autotools
(--disable-net --enable-static --disable-shared), and the resulting
libdogecoin.a + include/libdogecoin.h are placed in lib/ and include/.
Pass --sha256=<hex> to pin the source tarball checksum; omitted means we
print the hash for manual review.

Usage:
  python3 fetch.py --host=x86_64-pc-linux-gnu --tag=0.1.0   # binary release
  python3 fetch.py --host=x86_64-pc-linux-gnu --tag=0.1.1   # source build
  python3 fetch.py --host=x86_64-pc-linux-gnu --tag=0.1.1 --sha256=<hash>
"""
import glob
import hashlib
import os
import shutil
import subprocess
import sys
import tarfile
import zipfile
from io import BytesIO
from pathlib import Path

import requests
import argparse

VALID_HOSTS = (
    "arm-linux-gnueabihf",
    "aarch64-linux-gnu",
    "x86_64-pc-linux-gnu",
    "x86_64-apple-darwin14",
    "x86_64-w64-mingw32",
    "i686-w64-mingw32",
    "i686-pc-linux-gnu",
)

GITHUB_BASE = "https://github.com/dogecoinfoundation/libdogecoin"

GREEN = "\033[1;32m"
RED   = "\033[31m"
RESET = "\033[0m"


def ok(msg):  print(f"{GREEN}> {msg}{RESET}")
def err(msg): print(f"{RED}> {msg}{RESET}"); sys.exit(1)


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def get(url: str) -> requests.Response:
    r = requests.get(url)
    r.raise_for_status()
    return r


# ---------------------------------------------------------------------------
# Binary release path
# ---------------------------------------------------------------------------

def fetch_binary(tag: str, host: str):
    ext = ".zip" if "mingw32" in host else ".tar.gz"
    filename = f"libdogecoin-{tag}-{host}{ext}"
    base_url = f"{GITHUB_BASE}/releases/download/v{tag}/"

    # download and parse SHA256SUMS.asc
    checksums_text = get(base_url + "SHA256SUMS.asc").text
    ok("Downloaded SHA256SUMS.asc")

    # download archive
    archive_bytes = get(base_url + filename).content
    with open(filename, "wb") as f:
        f.write(archive_bytes)
    ok(f"Downloaded {filename}")

    # verify against SHA256SUMS.asc
    actual = sha256_of(archive_bytes)
    expected = None
    for line in checksums_text.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1] == filename:
            expected = parts[0]
            break

    if expected is None:
        err(f"{filename} not listed in SHA256SUMS.asc")
    if actual != expected:
        err(f"Checksum mismatch!\n  expected: {expected}\n  actual:   {actual}")
    ok("Checksum OK")

    # extract lib/ and include/
    os.makedirs("lib", exist_ok=True)
    os.makedirs("include", exist_ok=True)
    prefix = f"libdogecoin-{tag}-{host}"
    if ext == ".zip":
        with zipfile.ZipFile(BytesIO(archive_bytes)) as zf:
            zf.extractall(".")
    else:
        with tarfile.open(fileobj=BytesIO(archive_bytes), mode="r:gz") as tf:
            tf.extractall(".")

    for src, dst in [
        (f"{prefix}/lib/libdogecoin.a",   "lib/libdogecoin.a"),
        (f"{prefix}/include/libdogecoin.h", "include/libdogecoin.h"),
    ]:
        if os.path.isfile(src):
            os.replace(src, dst)


# ---------------------------------------------------------------------------
# Source-only release path
# ---------------------------------------------------------------------------

def build_from_source(tag: str, host: str, expected_sha256: str | None):
    src_url = f"{GITHUB_BASE}/archive/refs/tags/v{tag}.tar.gz"
    print(f"Downloading source tarball for v{tag} ...")
    src_bytes = get(src_url).content
    actual = sha256_of(src_bytes)

    if expected_sha256:
        if actual != expected_sha256.lower():
            err(f"Source tarball checksum mismatch!\n  expected: {expected_sha256}\n  actual:   {actual}")
        ok(f"Source tarball checksum OK ({actual})")
    else:
        print(f"\033[33m> Source tarball SHA256: {actual}")
        print(f"> Pass --sha256={actual} to pin this for reproducible builds.{RESET}")

    src_dir = f"libdogecoin-{tag}"
    with tarfile.open(fileobj=BytesIO(src_bytes), mode="r:gz") as tf:
        tf.extractall(".")
    ok(f"Extracted {src_dir}/")

    configure_args = [
        "./configure",
        "--disable-net",
        "--enable-static",
        "--disable-shared",
    ]
    # cross-compilation: pass --host only when not building natively
    native_hosts = {"x86_64-pc-linux-gnu", "i686-pc-linux-gnu",
                    "aarch64-linux-gnu", "arm-linux-gnueabihf"}
    if host not in native_hosts or host != _native_triplet():
        configure_args.append(f"--host={host}")

    print("Running autogen.sh ...")
    subprocess.run(["./autogen.sh"], cwd=src_dir, check=True)
    print("Running configure ...")
    subprocess.run(configure_args, cwd=src_dir, check=True)
    print(f"Building with make -j{os.cpu_count()} ...")
    subprocess.run(["make", f"-j{os.cpu_count()}"], cwd=src_dir, check=True)

    # locate the built static archive
    lib_candidates = [
        f"{src_dir}/.libs/libdogecoin.a",
        f"{src_dir}/src/.libs/libdogecoin.a",
        f"{src_dir}/libdogecoin.a",
    ]
    lib_src = next((p for p in lib_candidates if os.path.isfile(p)), None)
    if lib_src is None:
        err("Build finished but libdogecoin.a not found in expected locations")

    # v0.1.1+ moved the header under include/dogecoin/; flatten to include/
    hdr_candidates = [
        f"{src_dir}/include/dogecoin/libdogecoin.h",
        f"{src_dir}/include/libdogecoin.h",
    ]
    hdr_src = next((p for p in hdr_candidates if os.path.isfile(p)), None)
    if hdr_src is None:
        err("Build finished but libdogecoin.h not found in expected locations")

    os.makedirs("lib", exist_ok=True)
    os.makedirs("include", exist_ok=True)
    shutil.copy2(lib_src, "lib/libdogecoin.a")
    shutil.copy2(hdr_src, "include/libdogecoin.h")
    ok(f"Installed lib/libdogecoin.a and include/libdogecoin.h")


def _native_triplet() -> str:
    """Best-effort native host triplet via config.guess."""
    try:
        out = subprocess.check_output(
            ["bash", "-c", "cc -dumpmachine"], stderr=subprocess.DEVNULL)
        return out.decode().strip()
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

def cleanup(tag: str, host: str):
    patterns = [
        f"./libdogecoin-{tag}-{host}*",
        f"./libdogecoin-{tag}",
        "./__pycache__", "*.egg-info",
        "*.tar.gz", "*.zip", "*.c",
        "SHA256SUMS.asc",
    ]
    for pattern in patterns:
        for name in glob.glob(pattern):
            if os.path.isdir(name):
                shutil.rmtree(name, ignore_errors=True)
            elif os.path.isfile(name):
                os.remove(name)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", required=True,
                        help="target host triplet (e.g. x86_64-pc-linux-gnu)")
    parser.add_argument("--tag", default=None,
                        help="libdogecoin release tag (e.g. 0.1.1); "
                             "defaults to version in setup.py")
    parser.add_argument("--sha256", default=None,
                        help="expected SHA256 of the source tarball "
                             "(source-only releases; ignored for binary releases)")
    args = parser.parse_args()

    host = args.host
    assert host in VALID_HOSTS, f"Invalid host triplet: {host!r}"

    if args.tag:
        tag = args.tag.lstrip("v")
    else:
        import re
        setup_src = open(os.path.join(os.path.dirname(__file__), "setup.py")).read()
        m = re.search(r'version\s*=\s*["\']([^"\']+)["\']', setup_src)
        tag = m.group(1) if m else "0.1.1"

    print(f"Fetching libdogecoin v{tag} for {host}")

    # probe whether this tag has binary release assets
    checksums_url = f"{GITHUB_BASE}/releases/download/v{tag}/SHA256SUMS.asc"
    probe = requests.head(checksums_url, allow_redirects=True)

    if probe.status_code == 200:
        print("Binary release detected — fetching pre-built archive.")
        fetch_binary(tag, host)
    elif probe.status_code == 404:
        print("No binary release assets found — building from source.")
        build_from_source(tag, host, args.sha256)
    else:
        err(f"Unexpected HTTP {probe.status_code} probing {checksums_url}")

    cleanup(tag, host)
    ok(f"libdogecoin v{tag} ready in lib/ and include/")


if __name__ == "__main__":
    main()
