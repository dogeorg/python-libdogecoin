"""Tests for the 0.1.5-pre additions: explicit-buffer (`_ex`) transaction
variants and BIP39 mnemonic verification.

The `_ex` functions take a caller-provided buffer instead of returning a pointer
into a static library-owned buffer. The strongest correctness check is
*equivalence*: each `_ex` variant must produce byte-identical output to its
established non-`_ex` counterpart on the same inputs (the non-`_ex` results are
already pinned to known-answer hex vectors in transaction_test.py). If the
buffer plumbing — capacity, the in/out size pointer, argument order — were
wrong, the output would differ or be truncated, and these tests would catch it.

These skip cleanly on libdogecoin builds that predate the `_ex`/verify_mnemonic
surface, so the suite stays green against older C-libraries.
"""
import unittest

import libdogecoin as l

# Shared known-answer vectors and inputs (same values transaction_test.py uses).
privkey_wif = "ci5prbqz7jXyFPVWKkHhPq4a9N8Dag3TpeRfuqqC2Nfr7gSqx1fy"
bad_privkey_wif = "ci5prbqz7jXyFPVWKkHhPq4a9N8Dag3TpeRfuqqC2Nfr7gSqx1fx"
p2pkh_addr = "noxKJyGPugPRN4wqvrwsrtYXuQCk7yQEsy"
external_p2pkh_addr = "nbGfXLskPh7eM1iG5zz5EfDkkNTo9TRmde"
utxo_scriptpubkey = "76a914d8c43e6f68ca4ea1e9b93da2d1e3a95118fa4a7c88ac"

hash_2_doge = "b4455e7b7b7acb51fb6feba7a2702c42a5100f61f61abafa31851ed6ae076074"
hash_10_doge = "42113bdc65fc2943cf0359ea1a24ced0b6b0b5290db4c63a3329c6601c4616e2"
vout = 1
send_amt = "5"
fee = "0.00226"
total_utxo_input = "12"

expected_unsigned_double_utxo_single_output_tx_hex = (
    "0100000002746007aed61e8531faba1af6610f10a5422c70a2a7eb6ffb51cb7a7b7b5e45b4"
    "0100000000ffffffffe216461c60c629333ac6b40d29b5b0b6d0ce241aea5903cf4329fc65"
    "dc3b11420100000000ffffffff010065cd1d000000001976a9144da2f8202789567d402f7f"
    "717c01d98837e4325488ac00000000")
expected_unsigned_tx_hex = (
    "0100000002746007aed61e8531faba1af6610f10a5422c70a2a7eb6ffb51cb7a7b7b5e45b4"
    "0100000000ffffffffe216461c60c629333ac6b40d29b5b0b6d0ce241aea5903cf4329fc65"
    "dc3b11420100000000ffffffff020065cd1d000000001976a9144da2f8202789567d402f7f"
    "717c01d98837e4325488ac30b4b529000000001976a914d8c43e6f68ca4ea1e9b93da2d1e3"
    "a95118fa4a7c88ac00000000")
expected_signed_single_input_tx_hex = (
    "0100000002746007aed61e8531faba1af6610f10a5422c70a2a7eb6ffb51cb7a7b7b5e45b4"
    "010000006b48304502210090bddac300243d16dca5e38ab6c80d5848e0d710d77702223bac"
    "d6682654f6fe02201b5c2e8b1143d8a807d604dc18068b4278facce561c302b0c66a4f2a5a"
    "4aa66f0121031dc1e49cfa6ae15edd6fa871a91b1f768e6f6cab06bf7a87ac0d8beb922907"
    "5bffffffffe216461c60c629333ac6b40d29b5b0b6d0ce241aea5903cf4329fc65dc3b1142"
    "0100000000ffffffff020065cd1d000000001976a9144da2f8202789567d402f7f717c01d9"
    "8837e4325488ac30b4b529000000001976a914d8c43e6f68ca4ea1e9b93da2d1e3a95118fa"
    "4a7c88ac00000000")
expected_signed_raw_tx_hex = (
    "0100000002746007aed61e8531faba1af6610f10a5422c70a2a7eb6ffb51cb7a7b7b5e45b4"
    "010000006b48304502210090bddac300243d16dca5e38ab6c80d5848e0d710d77702223bac"
    "d6682654f6fe02201b5c2e8b1143d8a807d604dc18068b4278facce561c302b0c66a4f2a5a"
    "4aa66f0121031dc1e49cfa6ae15edd6fa871a91b1f768e6f6cab06bf7a87ac0d8beb922907"
    "5bffffffffe216461c60c629333ac6b40d29b5b0b6d0ce241aea5903cf4329fc65dc3b1142"
    "010000006a47304402200e19c2a66846109aaae4d29376040fc4f7af1a519156fe8da543dc"
    "6f03bb50a102203a27495aba9eead2f154e44c25b52ccbbedef084f0caf1deedaca87efd77"
    "e4e70121031dc1e49cfa6ae15edd6fa871a91b1f768e6f6cab06bf7a87ac0d8beb9229075b"
    "ffffffff020065cd1d000000001976a9144da2f8202789567d402f7f717c01d98837e43254"
    "88ac30b4b529000000001976a914d8c43e6f68ca4ea1e9b93da2d1e3a95118fa4a7c88ac00"
    "000000")

_HAS_EX = hasattr(l, "w_get_raw_transaction_ex")
_HAS_VERIFY_MNEMONIC = hasattr(l, "w_dogecoin_verify_mnemonic")


def _build_double_utxo_single_output():
    """Build the canonical 2-input/1-output working tx, return its index."""
    idx = l.w_start_transaction()
    l.w_add_utxo(idx, hash_2_doge, vout)
    l.w_add_utxo(idx, hash_10_doge, vout)
    l.w_add_output(idx, external_p2pkh_addr, send_amt)
    return idx


@unittest.skipUnless(_HAS_EX, "libdogecoin build lacks the _ex transaction surface")
class TestExplicitBufferEquivalence(unittest.TestCase):
    """Each _ex variant must produce byte-identical output to its non-_ex twin."""

    def setUp(self):
        # Restart the ECC context before each test: some _ex functions in
        # v0.1.5-pre call dogecoin_ecc_stop() as a side effect, leaving the
        # context dead for subsequent signing tests.
        l.w_context_stop()
        l.w_context_start()

    def tearDown(self):
        l.w_context_stop()

    def test_get_raw_transaction_ex_matches(self):
        idx = _build_double_utxo_single_output()
        try:
            base = l.w_get_raw_transaction(idx)
            ex = l.w_get_raw_transaction_ex(idx)
            self.assertEqual(ex, base)
            self.assertEqual(ex, expected_unsigned_double_utxo_single_output_tx_hex)
        finally:
            l.w_clear_transaction(idx)

    def test_finalize_transaction_ex_matches(self):
        idx_base = l.w_store_raw_transaction(
            expected_unsigned_double_utxo_single_output_tx_hex)
        idx_ex = l.w_store_raw_transaction(
            expected_unsigned_double_utxo_single_output_tx_hex)
        try:
            base = l.w_finalize_transaction(
                idx_base, external_p2pkh_addr, fee, total_utxo_input, p2pkh_addr)
            ex = l.w_finalize_transaction_ex(
                idx_ex, external_p2pkh_addr, fee, total_utxo_input, p2pkh_addr)
            self.assertEqual(ex, base)
            self.assertEqual(ex, expected_unsigned_tx_hex)
        finally:
            l.w_clear_transaction(idx_base)
            l.w_clear_transaction(idx_ex)

    def test_sign_raw_transaction_ex_matches(self):
        # single input
        base1 = l.w_sign_raw_transaction(
            0, expected_unsigned_tx_hex, utxo_scriptpubkey, 1, privkey_wif)
        ex1 = l.w_sign_raw_transaction_ex(
            0, expected_unsigned_tx_hex, utxo_scriptpubkey, 1, privkey_wif)
        self.assertEqual(ex1, base1)
        self.assertEqual(ex1, expected_signed_single_input_tx_hex)
        # second input, signing on top of the first
        base2 = l.w_sign_raw_transaction(
            1, expected_signed_single_input_tx_hex, utxo_scriptpubkey, 1, privkey_wif)
        ex2 = l.w_sign_raw_transaction_ex(
            1, expected_signed_single_input_tx_hex, utxo_scriptpubkey, 1, privkey_wif)
        self.assertEqual(ex2, base2)
        self.assertEqual(ex2, expected_signed_raw_tx_hex)

    def test_sign_indexed_raw_transaction_ex_signs(self):
        # sign_indexed_raw_transaction_ex(tx_index, input_index, ...) signs one
        # input of a STORED tx and returns the signed hex. Signing input 0 must
        # match w_sign_raw_transaction signing input 0 of the same raw tx.
        idx = l.w_store_raw_transaction(expected_unsigned_tx_hex)
        try:
            ex = l.w_sign_indexed_raw_transaction_ex(
                idx, 0, utxo_scriptpubkey, 1, privkey_wif)
            base = l.w_sign_raw_transaction(
                0, expected_unsigned_tx_hex, utxo_scriptpubkey, 1, privkey_wif)
            self.assertEqual(ex, base)
            self.assertEqual(ex, expected_signed_single_input_tx_hex)
        finally:
            l.w_clear_transaction(idx)

    def test_sign_transaction_ex_matches(self):
        # non-_ex w_sign_transaction returns an int status and mutates the stored
        # tx in place; _ex returns the signed hex directly. Equivalence: after the
        # non-_ex sign, the stored tx's raw hex must equal the _ex return value.
        idx_base = l.w_store_raw_transaction(expected_unsigned_tx_hex)
        idx_ex = l.w_store_raw_transaction(expected_unsigned_tx_hex)
        try:
            rc = l.w_sign_transaction(idx_base, utxo_scriptpubkey, privkey_wif)
            self.assertTrue(rc)
            base_hex = l.w_get_raw_transaction(idx_base)
            ex = l.w_sign_transaction_ex(idx_ex, utxo_scriptpubkey, privkey_wif)
            self.assertEqual(ex, base_hex)
        finally:
            l.w_clear_transaction(idx_base)
            l.w_clear_transaction(idx_ex)

    def test_sign_transaction_w_privkey_ex_signs(self):
        # NOTE: the non-_ex and _ex variants here have DIFFERENT signatures —
        # non-_ex w_sign_transaction_w_privkey(tx_index, vout_index, privkey)
        # signs one input and returns int; _ex w_sign_transaction_w_privkey_ex(
        # tx_index, privkey) signs the whole tx and returns hex. They are not a
        # drop-in pair, so assert the _ex result against the non-_ex whole-tx
        # signer's stored output instead.
        idx_base = l.w_store_raw_transaction(expected_unsigned_tx_hex)
        idx_ex = l.w_store_raw_transaction(expected_unsigned_tx_hex)
        try:
            rc = l.w_sign_transaction(idx_base, utxo_scriptpubkey, privkey_wif)
            self.assertTrue(rc)
            base_hex = l.w_get_raw_transaction(idx_base)
            ex = l.w_sign_transaction_w_privkey_ex(idx_ex, privkey_wif)
            self.assertEqual(ex, base_hex)
        finally:
            l.w_clear_transaction(idx_base)
            l.w_clear_transaction(idx_ex)


@unittest.skipUnless(_HAS_EX, "libdogecoin build lacks the _ex transaction surface")
class TestExplicitBufferEdgeCases(unittest.TestCase):

    def setUp(self):
        l.w_context_stop()
        l.w_context_start()

    def tearDown(self):
        l.w_context_stop()

    def test_get_raw_transaction_ex_bad_index(self):
        # a non-existent tx index returns None, not a partial/garbage buffer
        result = l.w_get_raw_transaction_ex(99999)
        self.assertIsNone(result)

    def test_sign_raw_transaction_ex_bad_privkey(self):
        # signing with a wrong key must fail (None), not return a malformed tx
        result = l.w_sign_raw_transaction_ex(
            0, expected_unsigned_tx_hex, utxo_scriptpubkey, 1, bad_privkey_wif)
        self.assertFalse(result)

    def test_full_signed_tx_not_truncated(self):
        # the signed double-input tx is ~430 bytes; confirm the explicit buffer
        # returns the complete hex (a too-small buffer would truncate it)
        ex = l.w_sign_raw_transaction_ex(
            0, expected_unsigned_tx_hex, utxo_scriptpubkey, 1, privkey_wif)
        ex = l.w_sign_raw_transaction_ex(
            1, ex, utxo_scriptpubkey, 1, privkey_wif)
        self.assertEqual(ex, expected_signed_raw_tx_hex)
        self.assertEqual(len(ex), len(expected_signed_raw_tx_hex))


@unittest.skipUnless(_HAS_VERIFY_MNEMONIC,
                     "libdogecoin build lacks dogecoin_verify_mnemonic")
class TestVerifyMnemonic(unittest.TestCase):
    """BIP39 mnemonic verification."""

    # canonical Trezor test vector (12-word, "abandon...about")
    VALID = ("abandon abandon abandon abandon abandon abandon "
             "abandon abandon abandon abandon abandon about")

    def test_valid_mnemonic_verifies(self):
        self.assertTrue(l.w_dogecoin_verify_mnemonic(self.VALID))

    def test_tampered_mnemonic_fails(self):
        # swap the last word for one that breaks the checksum
        tampered = self.VALID.rsplit(" ", 1)[0] + " zoo"
        self.assertFalse(l.w_dogecoin_verify_mnemonic(tampered))

    def test_garbage_mnemonic_fails(self):
        self.assertFalse(l.w_dogecoin_verify_mnemonic("not a real mnemonic phrase"))

    def test_wrong_word_count_fails(self):
        self.assertFalse(l.w_dogecoin_verify_mnemonic("abandon abandon abandon"))


if __name__ == "__main__":
    unittest.main()
