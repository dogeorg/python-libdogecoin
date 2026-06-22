"""Tier 3 Layer B tests: EC key / pubkey objects.

Covers generation, the WIF bridge to Tier 1, deriving a pubkey, sign/verify
round-trips, and — the security-critical property — that a private key's bytes
are wiped (cleansed) on explicit free and on context-manager exit.

Skips cleanly on libdogecoin builds lacking the key surface.
"""
import unittest

import libdogecoin as l

_HAS = getattr(l, "_HAS_TIER3", False) and hasattr(l, "Key")


@unittest.skipUnless(_HAS, "libdogecoin build lacks the dogecoin_key surface")
class TestKey(unittest.TestCase):

    def test_generate_is_valid(self):
        with l.Key.generate() as k:
            self.assertTrue(k.is_valid())
            self.assertEqual(len(k.private_bytes), 32)

    def test_wif_bridge_round_trip(self):
        with l.Key.generate() as k:
            wif = k.to_wif(l.MAINNET)
            self.assertIsInstance(wif, str)
            self.assertTrue(wif)
            k2 = l.Key.from_wif(wif, l.MAINNET)
            try:
                self.assertTrue(k2.is_valid())
            finally:
                k2.free()

    def test_pubkey_from_key(self):
        with l.Key.generate() as k:
            pub = k.pubkey()
            try:
                self.assertTrue(pub.is_valid())
                self.assertIsInstance(pub.hex(), str)
                self.assertEqual(len(pub.hash160()), 20)
            finally:
                pub.free()

    def test_sign_verify_round_trip(self):
        h = bytes([0xAB] * 32)
        with l.Key.generate() as k:
            sig = k.sign(h)
            self.assertIsInstance(sig, bytes)
            pub = k.pubkey()
            try:
                self.assertTrue(pub.verify(h, sig))
                self.assertFalse(pub.verify(bytes(32), sig))
            finally:
                pub.free()

    def test_sign_rejects_wrong_hash_length(self):
        with l.Key.generate() as k:
            with self.assertRaises(ValueError):
                k.sign(b"too short")


@unittest.skipUnless(_HAS, "libdogecoin build lacks the dogecoin_key surface")
class TestKeyCleanse(unittest.TestCase):
    """The security guarantee: secrets are wiped on release."""

    def test_free_wipes_private_bytes(self):
        k = l.Key.generate()
        before = k.private_bytes
        self.assertTrue(any(before), "generated key should be nonzero")
        # capture the cffi struct to inspect raw memory after cleanse
        from libdogecoin._libdogecoin_cffi import ffi  # type: ignore
        ptr = k._cptr
        k.free()
        after = bytes(ffi.buffer(ptr.privkey, 32))
        self.assertEqual(after, b"\x00" * 32, "private key not wiped on free")

    def test_context_exit_wipes_private_bytes(self):
        from libdogecoin._libdogecoin_cffi import ffi  # type: ignore
        with l.Key.generate() as k:
            ptr = k._cptr
            self.assertTrue(any(bytes(ffi.buffer(ptr.privkey, 32))))
        after = bytes(ffi.buffer(ptr.privkey, 32))
        self.assertEqual(after, b"\x00" * 32, "private key not wiped on exit")

    def test_use_after_free(self):
        k = l.Key.generate()
        k.free()
        with self.assertRaises(l.UseAfterFreeError):
            _ = k.private_bytes


if __name__ == "__main__":
    unittest.main()
