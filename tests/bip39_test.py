"""Known-answer tests for the BIP39 / seed / message-signing surface.

Unlike address_test.py (which checks shapes) these assert exact byte-level
output against published spec vectors, because a wrong seed silently derives
wrong addresses and loses funds. The canonical vector is the Trezor BIP39
reference: the 12-word all-"abandon" mnemonic with passphrase "TREZOR".

Functions in this group exist only when the package was built against a
libdogecoin release that exports them (BIP39 landed after v0.1.0). Each test
skips cleanly when its function is absent, so the file is correct on every
build.
"""
import unittest

import libdogecoin as l

# Canonical BIP39 vector (Trezor reference set, 128-bit entropy entry).
# Source: trezor/python-mnemonic vectors.json. Assumes libdogecoin derives the
# seed with the standard PBKDF2-HMAC-SHA512, 2048 iterations, salt
# "mnemonic"+passphrase. If this test fails against the real library, that is a
# signal libdogecoin deviates from standard BIP39 — which is exactly what a KAT
# is here to catch, not something to paper over by relaxing the assertion.
ABANDON_MNEMONIC = (
    "abandon abandon abandon abandon abandon abandon "
    "abandon abandon abandon abandon abandon about"
)
TREZOR_PASS = "TREZOR"
# Expected BIP39 seed for (ABANDON_MNEMONIC, "TREZOR"), 64 bytes, hex:
EXPECTED_SEED_HEX = (
    "c55257c360c07c72029aebc1b53c05ed0362ada38ead3e3e9efa3708e5349553"
    "1f09a6987599d18264c1e1c92f2cf141630c7a3c4ab7c81b2f001698e7463b04"
)


def _present(name: str) -> bool:
    """True if the underlying C function is in this build's surface."""
    try:
        return name in set(l.available())
    except Exception:
        return False


class TestBip39KnownAnswers(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        l.w_context_start()

    @classmethod
    def tearDownClass(cls):
        l.w_context_stop()

    def test_seed_from_mnemonic_matches_bip39_vector(self):
        """seed_from_mnemonic must reproduce the published BIP39 seed exactly."""
        if not _present("dogecoin_seed_from_mnemonic"):
            self.skipTest("dogecoin_seed_from_mnemonic not in this build")
        seed = l.w_dogecoin_seed_from_mnemonic(ABANDON_MNEMONIC, TREZOR_PASS)
        self.assertIsNotNone(seed)
        self.assertEqual(len(seed), 64, "BIP39 seed must be 64 bytes")
        self.assertEqual(seed.hex(), EXPECTED_SEED_HEX,
                         "seed does not match the BIP39 reference vector")

    def test_seed_empty_passphrase_differs_from_trezor(self):
        """A different passphrase must yield a different seed (no silent ignore)."""
        if not _present("dogecoin_seed_from_mnemonic"):
            self.skipTest("dogecoin_seed_from_mnemonic not in this build")
        seed_default = l.w_dogecoin_seed_from_mnemonic(ABANDON_MNEMONIC, "")
        seed_trezor = l.w_dogecoin_seed_from_mnemonic(ABANDON_MNEMONIC, TREZOR_PASS)
        self.assertIsNotNone(seed_default)
        self.assertNotEqual(seed_default.hex(), seed_trezor.hex(),
                            "passphrase must affect the derived seed")

    def test_random_mnemonic_word_count(self):
        """A 128-bit random mnemonic is 12 words; 256-bit is 24."""
        if not _present("generateRandomEnglishMnemonic"):
            self.skipTest("generateRandomEnglishMnemonic not in this build")
        m128 = l.w_generate_random_english_mnemonic("128")
        self.assertIsNotNone(m128)
        self.assertEqual(len(m128.split()), 12)
        m256 = l.w_generate_random_english_mnemonic("256")
        self.assertIsNotNone(m256)
        self.assertEqual(len(m256.split()), 24)

    def test_generated_mnemonic_round_trips_to_seed(self):
        """A freshly generated mnemonic must derive a valid 64-byte seed."""
        if not (_present("generateRandomEnglishMnemonic")
                and _present("dogecoin_seed_from_mnemonic")):
            self.skipTest("mnemonic/seed pair not in this build")
        m = l.w_generate_random_english_mnemonic("128")
        seed = l.w_dogecoin_seed_from_mnemonic(m, "")
        self.assertIsNotNone(seed)
        self.assertEqual(len(seed), 64)


class TestMessageSigning(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        l.w_context_start()

    @classmethod
    def tearDownClass(cls):
        l.w_context_stop()

    def test_sign_then_verify_round_trip(self):
        """A message signed by a key must verify against that key's address."""
        if not (_present("sign_message") and _present("verify_message")):
            self.skipTest("message signing not in this build")
        privkey, address = l.w_generate_priv_pub_key_pair()
        sig = l.w_sign_message(privkey, "the grumpy wizard makes a brew")
        self.assertIsNotNone(sig)
        self.assertTrue(l.w_verify_message(sig, "the grumpy wizard makes a brew", address))

    def test_verify_rejects_tampered_message(self):
        """A valid signature must not verify against a different message."""
        if not (_present("sign_message") and _present("verify_message")):
            self.skipTest("message signing not in this build")
        privkey, address = l.w_generate_priv_pub_key_pair()
        sig = l.w_sign_message(privkey, "original message")
        self.assertFalse(l.w_verify_message(sig, "tampered message", address))


if __name__ == "__main__":
    unittest.main()
