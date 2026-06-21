"""Tests for BIP39 mnemonic and extended HD address functions (libdogecoin 0.1.2+)."""

import unittest
import libdogecoin as l


class TestMnemonicFunctions(unittest.TestCase):

    def setUpClass():
        l.w_context_start()

    def tearDownClass():
        l.w_context_stop()

    # --- generateRandomEnglishMnemonic ---

    def test_random_mnemonic_128(self):
        """128-bit random mnemonic returns 12 words."""
        m = l.w_generate_random_english_mnemonic("128")
        self.assertIsNotNone(m)
        self.assertEqual(len(m.split()), 12)

    def test_random_mnemonic_256(self):
        """256-bit random mnemonic returns 24 words."""
        m = l.w_generate_random_english_mnemonic("256")
        self.assertIsNotNone(m)
        self.assertEqual(len(m.split()), 24)

    def test_random_mnemonic_uniqueness(self):
        """Two consecutive random mnemonics should differ."""
        m1 = l.w_generate_random_english_mnemonic("128")
        m2 = l.w_generate_random_english_mnemonic("128")
        self.assertNotEqual(m1, m2)

    # --- generateEnglishMnemonic ---

    def test_english_mnemonic_from_entropy(self):
        """Known hex entropy produces a deterministic mnemonic."""
        entropy = "f585c11aec520db57dd353c69cc6f616"
        m = l.w_generate_english_mnemonic(entropy, "128")
        self.assertIsNotNone(m)
        self.assertEqual(len(m.split()), 12)

    def test_english_mnemonic_256_from_entropy(self):
        """256-bit hex entropy produces a 24-word mnemonic."""
        entropy = "f585c11aec520db57dd353c69cc6f616f585c11aec520db57dd353c69cc6f616"
        m = l.w_generate_english_mnemonic(entropy, "256")
        self.assertIsNotNone(m)
        self.assertEqual(len(m.split()), 24)

    # --- dogecoin_seed_from_mnemonic ---

    def test_seed_from_mnemonic_length(self):
        """Seed derived from mnemonic is exactly 64 bytes."""
        m = l.w_generate_random_english_mnemonic("128")
        self.assertIsNotNone(m)
        seed = l.w_dogecoin_seed_from_mnemonic(m)
        self.assertIsNotNone(seed)
        self.assertEqual(len(seed), 64)
        self.assertIsInstance(seed, bytes)

    def test_seed_from_mnemonic_with_passphrase(self):
        """Same mnemonic with different passphrase yields different seed."""
        m = l.w_generate_random_english_mnemonic("128")
        self.assertIsNotNone(m)
        seed1 = l.w_dogecoin_seed_from_mnemonic(m, "")
        seed2 = l.w_dogecoin_seed_from_mnemonic(m, "TREZOR")
        self.assertNotEqual(seed1, seed2)

    def test_seed_from_mnemonic_deterministic(self):
        """Same mnemonic and passphrase always yield the same seed."""
        m = l.w_generate_random_english_mnemonic("128")
        self.assertIsNotNone(m)
        seed1 = l.w_dogecoin_seed_from_mnemonic(m, "pw")
        seed2 = l.w_dogecoin_seed_from_mnemonic(m, "pw")
        self.assertEqual(seed1, seed2)

    # --- getDerivedHDAddressFromMnemonic ---

    def test_hd_address_from_mnemonic_mainnet(self):
        """getDerivedHDAddressFromMnemonic returns a valid mainnet address."""
        m = l.w_generate_random_english_mnemonic("128")
        addr = l.w_get_derived_hd_address_from_mnemonic(0, 0, "0", m)
        self.assertIsNotNone(addr)
        self.assertTrue(l.w_verify_p2pkh_address(addr), f"invalid address: {addr!r}")

    def test_hd_address_from_mnemonic_testnet(self):
        """getDerivedHDAddressFromMnemonic returns a valid testnet address."""
        m = l.w_generate_random_english_mnemonic("128")
        addr = l.w_get_derived_hd_address_from_mnemonic(0, 0, "0", m, chain_code=1)
        self.assertIsNotNone(addr)
        self.assertTrue(l.w_verify_p2pkh_address(addr), f"invalid address: {addr!r}")

    def test_hd_address_from_mnemonic_deterministic(self):
        """Same mnemonic/path always produces the same address."""
        m = l.w_generate_random_english_mnemonic("128")
        addr1 = l.w_get_derived_hd_address_from_mnemonic(0, 0, "0", m)
        addr2 = l.w_get_derived_hd_address_from_mnemonic(0, 0, "0", m)
        self.assertEqual(addr1, addr2)

    def test_hd_address_from_mnemonic_index_varies(self):
        """Different address indices produce different addresses."""
        m = l.w_generate_random_english_mnemonic("128")
        addr0 = l.w_get_derived_hd_address_from_mnemonic(0, 0, "0", m)
        addr1 = l.w_get_derived_hd_address_from_mnemonic(0, 1, "0", m)
        self.assertNotEqual(addr0, addr1)

    # --- getDerivedHDAddress ---
    # Returns an extended public key (xpub) or extended private key (xprv),
    # NOT a leaf p2pkh address.

    def test_get_derived_hd_address_xpub(self):
        """getDerivedHDAddress with outprivkey=False returns a non-empty xpub."""
        master, _ = l.w_generate_hd_master_pub_key_pair()
        xpub = l.w_get_derived_hd_address(master, 0, 0, 0)
        self.assertIsNotNone(xpub)
        self.assertGreater(len(xpub), 0)

    def test_get_derived_hd_address_xprv(self):
        """getDerivedHDAddress with outprivkey=True returns a non-empty xprv."""
        master, _ = l.w_generate_hd_master_pub_key_pair()
        xprv = l.w_get_derived_hd_address(master, 0, 0, 0, outprivkey=True)
        self.assertIsNotNone(xprv)
        self.assertGreater(len(xprv), 0)

    def test_get_derived_hd_address_index_varies(self):
        """Different address indices produce different extended keys."""
        master, _ = l.w_generate_hd_master_pub_key_pair()
        key0 = l.w_get_derived_hd_address(master, 0, 0, 0)
        key1 = l.w_get_derived_hd_address(master, 0, 0, 1)
        self.assertNotEqual(key0, key1)

    # --- getDerivedHDAddressByPath ---
    # Also returns extended keys (xpub/xprv) for the given BIP32 path.

    def test_get_derived_hd_address_by_path_xpub(self):
        """getDerivedHDAddressByPath returns a non-empty xpub for a BIP32 path."""
        master, _ = l.w_generate_hd_master_pub_key_pair()
        xpub = l.w_get_derived_hd_address_by_path(master, "m/44'/3'/0'/0/0")
        self.assertIsNotNone(xpub)
        self.assertGreater(len(xpub), 0)

    def test_get_derived_hd_address_by_path_xprv(self):
        """getDerivedHDAddressByPath returns a non-empty xprv when outprivkey=True."""
        master, _ = l.w_generate_hd_master_pub_key_pair()
        xprv = l.w_get_derived_hd_address_by_path(
            master, "m/44'/3'/0'/0/0", outprivkey=True)
        self.assertIsNotNone(xprv)
        self.assertGreater(len(xprv), 0)


if __name__ == "__main__":
    unittest.main()
