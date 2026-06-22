"""Known-answer tests for ECDSA signing (Layer B).

libdogecoin signs via libsecp256k1 with RFC 6979 deterministic nonces
(src/ecc.c: secp256k1_ecdsa_sign(..., secp256k1_nonce_function_rfc6979, NULL)),
so a given private key and message hash yield a *fixed* DER signature. These
tests assert the exact signature bytes, not just a sign/verify round-trip — a
deviation means the binding (or the linked library) is not producing
RFC-6979-correct signatures, which for a wallet is a fund-safety bug.

Vector: the canonical secp256k1 RFC 6979 vector for message "sample".
  private key x = c9afa9d8...120f6721  (the RFC 6979 example key)
  hash = SHA256("sample") = af2bdbe1...62add1bf
  r = 432310e3...fcd7a6c8   s = 530128b6...02bfab69
The r/s here are the secp256k1 values (the RFC's published r/s are for
NIST P-256); these were cross-checked against libsecp256k1 directly.

Skips on builds lacking the key surface.
"""
import hashlib
import unittest

import libdogecoin as l

_HAS = getattr(l, "_HAS_TIER3", False) and hasattr(l, "Key")

PRIVKEY = bytes.fromhex(
    "c9afa9d845ba75166b5c215767b1d6934e50c3db36e89b127b8a622b120f6721")
MSG = b"sample"
HASH = bytes.fromhex(
    "af2bdbe1aa9b6ec1e2ade1d694f41fc71a831d0268e9891562113d8a62add1bf")
# DER( r=432310e3..fcd7a6c8 , s=530128b6..02bfab69 ), as libsecp256k1 emits it.
EXPECTED_DER = bytes.fromhex(
    "30440220432310e32cb80eb6503a26ce83cc165c783b870845fb8aad6d970889"
    "fcd7a6c80220530128b6b81c548874a6305d93ed071ca6e05074d85863d4056c"
    "e89b02bfab69")


@unittest.skipUnless(_HAS, "libdogecoin build lacks the dogecoin_key surface")
class TestEcdsaKnownAnswer(unittest.TestCase):

    def setUp(self):
        # the context must be live for key ops
        l.w_context_start()
        self.addCleanup(l.w_context_stop)

    def test_hash_is_the_expected_vector(self):
        self.assertEqual(hashlib.sha256(MSG).digest(), HASH)

    def test_deterministic_signature_exact_match(self):
        """The RFC6979 signature must equal the published secp256k1 bytes."""
        with l.Key.from_bytes(PRIVKEY) as k:
            sig = k.sign(HASH)
        self.assertEqual(
            sig.hex(), EXPECTED_DER.hex(),
            "signature does not match the RFC6979 secp256k1 vector — the "
            "library is not signing deterministically/correctly")

    def test_signature_is_stable_across_calls(self):
        """Determinism: signing the same hash twice yields identical bytes."""
        with l.Key.from_bytes(PRIVKEY) as k:
            self.assertEqual(k.sign(HASH), k.sign(HASH))

    def test_known_key_verifies_its_signature(self):
        with l.Key.from_bytes(PRIVKEY) as k:
            sig = k.sign(HASH)
            pub = k.pubkey()
            try:
                self.assertTrue(pub.verify(HASH, sig))
                # tamper one byte of the hash -> must not verify
                bad = bytearray(HASH); bad[0] ^= 0xFF
                self.assertFalse(pub.verify(bytes(bad), sig))
            finally:
                pub.free()


if __name__ == "__main__":
    unittest.main()
