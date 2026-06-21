"""Tests for 0.1.3 address / pubkey / HD / koinu wrappers."""

import unittest
import libdogecoin as l


class TestAddressUtils013(unittest.TestCase):

    def setUpClass():
        l.w_context_start()

    def tearDownClass():
        l.w_context_stop()

    # --- b58 prefix checks ---

    def test_mainnet_address_is_mainnet(self):
        _, addr = l.w_generate_priv_pub_key_pair()
        self.assertTrue(l.w_is_mainnet_from_b58prefix(addr))

    def test_mainnet_address_is_not_testnet(self):
        _, addr = l.w_generate_priv_pub_key_pair()
        self.assertFalse(l.w_is_testnet_from_b58prefix(addr))

    def test_testnet_address_is_testnet(self):
        _, addr = l.w_generate_priv_pub_key_pair(chain_code=1)
        self.assertTrue(l.w_is_testnet_from_b58prefix(addr))

    # --- pubkey / privkey round-trips ---

    def test_get_pubkey_from_privkey_mainnet(self):
        wif, _ = l.w_generate_priv_pub_key_pair()
        pubkey = l.w_get_pubkey_from_privkey(wif)
        self.assertIsNotNone(pubkey)
        self.assertEqual(len(pubkey), 66)   # 33-byte compressed key in hex

    def test_get_pubkey_from_privkey_testnet(self):
        wif, _ = l.w_generate_priv_pub_key_pair(chain_code=1)
        pubkey = l.w_get_pubkey_from_privkey(wif, is_testnet=True)
        self.assertIsNotNone(pubkey)

    def test_get_address_from_pubkey_mainnet(self):
        wif, expected_addr = l.w_generate_priv_pub_key_pair()
        pubkey = l.w_get_pubkey_from_privkey(wif)
        addr = l.w_get_address_from_pubkey(pubkey)
        self.assertEqual(addr, expected_addr)

    def test_gen_privkey_mainnet(self):
        result = l.w_gen_privkey()
        self.assertIsNotNone(result)
        wif, hex_key = result
        self.assertTrue(wif.startswith("Q") or wif.startswith("6"))
        self.assertEqual(len(hex_key), 64)

    # --- pubkey hash round-trips ---

    def test_dogecoin_address_to_pubkey_hash(self):
        _, addr = l.w_generate_priv_pub_key_pair()
        h = l.w_dogecoin_address_to_pubkey_hash(addr)
        self.assertIsNotNone(h)
        self.assertGreater(len(h), 0)

    def test_dogecoin_p2pkh_address_to_pubkey_hash(self):
        _, addr = l.w_generate_priv_pub_key_pair()
        h = l.w_dogecoin_p2pkh_address_to_pubkey_hash(addr)
        self.assertIsNotNone(h)

    def test_get_addr_from_pubkey_hash_roundtrip(self):
        _, addr = l.w_generate_priv_pub_key_pair()
        h = l.w_dogecoin_p2pkh_address_to_pubkey_hash(addr)
        recovered = l.w_get_addr_from_pubkey_hash(h)
        self.assertEqual(recovered, addr)

    # --- WIF encode/decode ---

    def test_wif_encode_decode_roundtrip(self):
        result = l.w_gen_privkey()
        self.assertIsNotNone(result)
        wif_orig, hex_key = result
        wif_enc = l.w_get_wif_encoded_privkey(hex_key)
        self.assertEqual(wif_enc, wif_orig)
        hex_dec = l.w_get_decoded_privkey_wif(wif_enc)
        self.assertEqual(hex_dec, hex_key)


class TestHDUtils013(unittest.TestCase):

    def setUpClass():
        l.w_context_start()

    def tearDownClass():
        l.w_context_stop()

    def test_get_hd_root_key_from_seed(self):
        mnemonic = l.w_generate_random_english_mnemonic("128")
        seed = l.w_dogecoin_seed_from_mnemonic(mnemonic)
        masterkey = l.w_get_hd_root_key_from_seed(seed)
        self.assertIsNotNone(masterkey)
        self.assertGreater(len(masterkey), 0)

    def test_gen_hd_master(self):
        masterkey = l.w_gen_hd_master()
        self.assertIsNotNone(masterkey)

    def test_get_hd_pub_key(self):
        masterkey, _ = l.w_generate_hd_master_pub_key_pair()
        xpub = l.w_get_hd_pub_key(masterkey)
        self.assertIsNotNone(xpub)

    def test_derive_ext_key_from_hd_key(self):
        masterkey, _ = l.w_generate_hd_master_pub_key_pair()
        child = l.w_derive_ext_key_from_hd_key(masterkey, "m/44'/3'/0'")
        self.assertIsNotNone(child)

    def test_derive_ext_pub_key_from_hd_key(self):
        masterkey, _ = l.w_generate_hd_master_pub_key_pair()
        xpub = l.w_get_hd_pub_key(masterkey)
        child_pub = l.w_derive_ext_pub_key_from_hd_key(xpub, "m/0")
        self.assertIsNotNone(child_pub)

    def test_derive_hd_ext_from_master(self):
        masterkey, _ = l.w_generate_hd_master_pub_key_pair()
        child = l.w_derive_hd_ext_from_master(masterkey, "m/44'/3'/0'")
        self.assertIsNotNone(child)

    def test_bip44_extended_key(self):
        masterkey, _ = l.w_generate_hd_master_pub_key_pair()
        result = l.w_derive_bip44_extended_key(masterkey, 0, "0", 0)
        self.assertIsNotNone(result)
        extkey, keypath = result
        self.assertGreater(len(extkey), 0)
        self.assertGreater(len(keypath), 0)

    def test_bip44_extended_public_key(self):
        masterkey, _ = l.w_generate_hd_master_pub_key_pair()
        result = l.w_derive_bip44_extended_public_key(masterkey, 0, "0", 0)
        self.assertIsNotNone(result)
        extpub, keypath = result
        self.assertGreater(len(extpub), 0)


class TestKoinuUtils013(unittest.TestCase):

    def test_koinu_to_coins_str(self):
        s = l.w_koinu_to_coins_str(100_000_000)
        self.assertIsNotNone(s)
        self.assertAlmostEqual(float(s), 1.0, places=5)

    def test_coins_to_koinu_str(self):
        k = l.w_coins_to_koinu_str("1.0")
        self.assertEqual(k, 100_000_000)

    def test_koinu_coins_roundtrip(self):
        koinu = 123_456_789
        s = l.w_koinu_to_coins_str(koinu)
        k2 = l.w_coins_to_koinu_str(s)
        self.assertEqual(k2, koinu)

    def test_zero_koinu(self):
        s = l.w_koinu_to_coins_str(0)
        self.assertIsNotNone(s)
        self.assertEqual(float(s), 0.0)


if __name__ == "__main__":
    unittest.main()
