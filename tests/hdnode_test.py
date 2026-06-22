"""Tier 3 tests: HD node object + handle lifetime.

These exercise the object-oriented handle API (construction, derivation,
serialization, struct-field reads) and the lifetime guarantees of the _Handle
base (explicit free, context-manager scope, GC backstop, use-after-free).

The HD node surface exists only on libdogecoin builds that export
dogecoin_hdnode_*; the whole module skips cleanly otherwise, so it is correct
across releases.
"""
import gc
import unittest

import libdogecoin as l

_HAS = getattr(l, "_HAS_TIER3", False)

# BIP32 reference seed (the first BIP32 test vector's seed).
SEED = bytes.fromhex("000102030405060708090a0b0c0d0e0f")


def setup_module(_):
    l.w_context_start()


def teardown_module(_):
    l.w_context_stop()


@unittest.skipUnless(_HAS, "libdogecoin build lacks the dogecoin_hdnode surface")
class TestHDNode(unittest.TestCase):

    def test_from_seed_reads_fields(self):
        with l.HDNode.from_seed(SEED) as m:
            self.assertEqual(m.depth, 0)
            self.assertEqual(len(m.public_key), 33)
            self.assertEqual(len(m.chain_code), 32)
            self.assertEqual(len(m.private_key), 32)

    def test_derive_does_not_mutate_receiver(self):
        # libdogecoin's CKD mutates in place; the wrapper must copy first so the
        # parent node is unchanged after deriving a child.
        with l.HDNode.from_seed(SEED) as m:
            child = m.derive_private(5)
            try:
                self.assertEqual(m.depth, 0, "parent was mutated by derive")
                self.assertEqual(child.depth, 1)
                self.assertEqual(child.child_num, 5)
            finally:
                child.free()

    def test_serialize_round_trip(self):
        with l.HDNode.from_seed(SEED) as m:
            priv = m.serialize_private(l.MAINNET)
            self.assertIsInstance(priv, str)
            self.assertTrue(priv)
            back = l.HDNode.deserialize(priv, l.MAINNET)
            try:
                self.assertEqual(back.depth, m.depth)
            finally:
                back.free()

    def test_chainparams_distinct(self):
        self.assertNotEqual(l.MAINNET.name, l.TESTNET.name)
        self.assertIsNotNone(l.MAINNET._ptr)


@unittest.skipUnless(_HAS, "libdogecoin build lacks the dogecoin_hdnode surface")
class TestHandleLifetime(unittest.TestCase):

    def test_explicit_free_is_idempotent(self):
        m = l.HDNode.from_seed(SEED)
        m.free()
        m.free()  # must not raise or double-free
        self.assertTrue(m.closed)

    def test_use_after_free_raises(self):
        m = l.HDNode.from_seed(SEED)
        m.free()
        with self.assertRaises(l.UseAfterFreeError):
            _ = m.depth

    def test_context_manager_frees(self):
        with l.HDNode.from_seed(SEED) as m:
            self.assertFalse(m.closed)
        self.assertTrue(m.closed)

    def test_gc_backstop_does_not_crash(self):
        # a forgotten handle should be freed by the finalizer at GC time
        def make_and_drop():
            l.HDNode.from_seed(SEED)
        make_and_drop()
        gc.collect()  # must not crash / double-free


if __name__ == "__main__":
    unittest.main()
