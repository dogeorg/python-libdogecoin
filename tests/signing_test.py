"""Tests for message signing/verification (libdogecoin 0.1.2+)."""

import unittest
import libdogecoin as l


# Fixed keypair for deterministic signing tests
_PRIVKEY = None
_ADDRESS = None


def _get_keypair():
    global _PRIVKEY, _ADDRESS
    if _PRIVKEY is None:
        _PRIVKEY, _ADDRESS = l.w_generate_priv_pub_key_pair()
    return _PRIVKEY, _ADDRESS


class TestSigningFunctions(unittest.TestCase):

    def setUpClass():
        l.w_context_start()
        _get_keypair()

    def tearDownClass():
        l.w_context_stop()

    def test_sign_message_returns_string(self):
        """sign_message returns a non-empty string."""
        privkey, _ = _get_keypair()
        sig = l.w_sign_message(privkey, "hello dogecoin")
        self.assertIsNotNone(sig)
        self.assertIsInstance(sig, str)
        self.assertGreater(len(sig), 0)

    def test_verify_message_valid(self):
        """A signature produced by sign_message verifies correctly."""
        privkey, address = _get_keypair()
        msg = "hello dogecoin"
        sig = l.w_sign_message(privkey, msg)
        self.assertTrue(l.w_verify_message(sig, msg, address))

    def test_verify_message_wrong_message(self):
        """Verification fails when the message is altered."""
        privkey, address = _get_keypair()
        sig = l.w_sign_message(privkey, "hello dogecoin")
        self.assertFalse(l.w_verify_message(sig, "goodbye dogecoin", address))

    def test_verify_message_wrong_address(self):
        """Verification fails when a different address is supplied."""
        privkey, address = _get_keypair()
        _, other_address = l.w_generate_priv_pub_key_pair()
        sig = l.w_sign_message(privkey, "hello dogecoin")
        self.assertFalse(l.w_verify_message(sig, "hello dogecoin", other_address))

    def test_sign_message_empty_string(self):
        """Signing an empty message does not crash and returns a string."""
        privkey, address = _get_keypair()
        sig = l.w_sign_message(privkey, "")
        self.assertIsNotNone(sig)
        self.assertTrue(l.w_verify_message(sig, "", address))

    def test_sign_message_unicode(self):
        """Messages with non-ASCII characters can be signed and verified."""
        privkey, address = _get_keypair()
        msg = "such wow \U0001f436"
        sig = l.w_sign_message(privkey, msg)
        self.assertIsNotNone(sig)
        self.assertTrue(l.w_verify_message(sig, msg, address))

    def test_different_messages_different_signatures(self):
        """Different messages produce different signatures."""
        privkey, _ = _get_keypair()
        sig1 = l.w_sign_message(privkey, "message one")
        sig2 = l.w_sign_message(privkey, "message two")
        self.assertNotEqual(sig1, sig2)


if __name__ == "__main__":
    unittest.main()
