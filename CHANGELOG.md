# Changelog

All notable changes to `python-libdogecoin` are documented here. This project
adheres to [Semantic Versioning](https://semver.org/) and the bound C surface
tracks whichever libdogecoin release is fetched at build time.

## [Unreleased]

### Added
- Single stable-ABI (`abi3`) wheel per platform: one wheel now serves CPython
  3.10 through 3.13+, instead of an interpreter-specific wheel. Newer Python
  versions no longer fall back to a source build.
- `python_requires = ">=3.10"`, so older interpreters get a clear
  "no compatible version" message rather than a failing build.
- PEP 561 typing support: `py.typed` marker and `__init__.pyi` stubs for the
  full `w_*` API (including the BIP39/44, message-signing, and QR functions
  present on newer libdogecoin builds), enabling autocomplete and type checks
  in downstream code.
- BIP39 known-answer tests (`tests/bip39_test.py`) asserting the canonical
  Trezor reference seed vector byte-for-byte, plus message sign/verify
  round-trips. These guard the key-derivation path, where a wrong seed silently
  derives wrong addresses. Tests skip cleanly on builds that lack the functions.

### Changed
- PyPI uploads now use Trusted Publishing (OIDC) instead of a stored API token,
  removing a long-lived publish secret from CI. Requires a one-time publisher
  configuration on PyPI.
- Dropped vestigial Cython from the macOS and sdist CI dependency installs.

### Removed
- Root `libdogecoin.pyx` (byte-identical duplicate of `legacy/libdogecoin.pyx`,
  which is retained for provenance).

## [0.1.2] - 2026-06-21

### Added
- Expanded bound surface: BIP32 derivation by path, the BIP39 family
  (`w_generate_random_english_mnemonic`, `w_dogecoin_seed_from_mnemonic`,
  `w_get_derived_hd_address_from_mnemonic`), message signing
  (`w_sign_message`, `w_verify_message`), and QR generation. Available because
  the fetched libdogecoin release exports them; the binding picks them up
  automatically via the header-driven cdef.
- `available()` reports the C function names present in the current build.

## [0.1.1] - 2026-06-21

### Changed
- Build system migrated from Cython to CFFI. **The public `w_*` API is
  unchanged** and the bound surface is identical to 0.1.0 — this is a build and
  packaging change only, safe to adopt without code changes. The extension
  links the static libdogecoin archive at build time, so there is no shared
  `.so`/`.dll` dependency at runtime.
- The cdef is generated from the fetched libdogecoin header, so the bound
  surface tracks the pinned libdogecoin release rather than a hand-maintained
  list.

## [0.1.0.post1] - 2022-12-06

- Final Cython-based release. Address and stateful transaction wrappers over
  libdogecoin v0.1.0.

[Unreleased]: https://github.com/dogeorg/python-libdogecoin/compare/v0.1.2...HEAD
[0.1.2]: https://github.com/dogeorg/python-libdogecoin/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/dogeorg/python-libdogecoin/compare/v0.1.0.post1...v0.1.1
[0.1.0.post1]: https://github.com/dogeorg/python-libdogecoin/releases/tag/v0.1.0.post1
