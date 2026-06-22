# Changelog

All notable changes to `python-libdogecoin` are documented here. This project
adheres to [Semantic Versioning](https://semver.org/) and the bound C surface
tracks whichever libdogecoin release is fetched at build time.

## [0.1.3.2] - 2026-06-21

This release supersedes the broken 0.1.3. PyPI uploads are immutable, so 0.1.3
could not be corrected in place; the fix ships under a new version number,
0.1.3.2, while still building against libdogecoin **C-library 0.1.3** (there is
no C-library 0.1.3.2). The Python package version and the C-library tag are
intentionally decoupled — see `LIBDOGECOIN_TAG` in `fetch.py`.

### Removed
- Withdrew the partial SPV surface that shipped in 0.1.3:
  `w_dogecoin_get_balance`, `w_dogecoin_get_balance_str`,
  `w_dogecoin_get_utxo_txid_str`, and `w_dogecoin_unregister_watch_address`.
  These query a libdogecoin SPV node (`dogecoin_spv_client`) that the binding
  gives no way to create, configure, or run, and the `register` half of the
  register/unregister pair was never bound — so as shipped they could not
  function. A complete SPV binding (node lifecycle, register + unregister,
  balance/utxo queries) will land as one coherent feature in a later release.

### Added
- Codegen curation gate: SPV/net/wallet-node and TPM/secure-element functions
  are blocked from binding by name pattern unless explicitly opted into
  `ALLOW_BOUND`, so a deferred-subsystem function in a future libdogecoin header
  cannot ship by accident (as the SPV surface did). Held-back functions are
  reported in the build log and recorded under `deferred` in `_surface.json`.

### Fixed
- `fetch.py` now builds against an explicitly pinned `LIBDOGECOIN_TAG` instead
  of deriving the C-library tag from the Python package version. This is what
  lets the Python version (0.1.3.2) differ from the C-library tag (0.1.3) when
  a re-release forces a new package number.
- `bin/build` no longer hardcodes `libdogecoin-0.1.1`/`0.1.2` when unpacking the
  wheel to run tests; the directory is derived from the actual built version.
  Also dropped a stray `--tag-build=0.1.2` that appended a build tag to the
  version.

### Note
- 0.1.3 has been yanked on PyPI for the reason above. Installs resolve to
  0.1.3.2; anyone pinned to `==0.1.3` is unaffected. 0.1.1 and 0.1.2 never
  contained these functions and are unaffected.

## [Unreleased]

### Added
- Tier 3 key objects (Layer B): `Key` (EC private key) and `PubKey` on the same
  managed-handle base, plus sign/verify. `Key.generate()`, `Key.from_wif()` /
  `to_wif()` (bridging the Tier 1 string world), `pubkey()`, `sign(hash32)`,
  and `PubKey.verify(hash32, sig)` / `hex()` / `hash160()`. **Security:** a
  private key cleanses (zeroes) its secret bytes on explicit `free()`, on
  context-manager exit, and as a GC backstop — prefer `with Key.generate() as k:`
  so secrets do not linger in memory.
- Tier 3 object API (foundation): the HD (BIP32) node is now exposed as an
  `HDNode` object with managed lifetime, alongside `MAINNET`/`TESTNET`/`REGTEST`
  chain-parameter handles. Where the flat `w_*` functions take and return
  strings, `HDNode` lets you derive children, read struct fields
  (`depth`, `child_num`, `public_key`, ...), and serialize, e.g.
  `HDNode.from_seed(seed).derive_private(0).serialize_private(MAINNET)`.
  Lifetime is explicit-free-preferred with a GC finalizer backstop: handles
  support `with`, free exactly once, and raise `UseAfterFreeError` on use after
  free. This `_Handle` base is the foundation later struct types (key, pubkey,
  transaction, SPV client) build on. Imported only when the linked libdogecoin
  exposes the `dogecoin_hdnode_*` surface; the Tier 1 `w_*` API is unaffected.
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
