"""Offline, dependency-free checks for the committed POVU Vault contract.

Run: python -m unittest discover -s tests -v
These are *contract* tests, NOT proof local binary masters have been ingested.
"""
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
M = json.loads((ROOT / "manifests/canonical_assets.json").read_text(encoding="utf-8"))

class CanonicalInventoryTests(unittest.TestCase):
    def test_two_heroes_and_seven_villains(self):
        chars = M["characters"]
        self.assertEqual(len(chars), 9)
        self.assertEqual(sum(c["role"] == "hero" for c in chars), 2)
        self.assertEqual(sum(c["role"] == "villain" for c in chars), 7)
        self.assertEqual(len({c["id"] for c in chars}), 9)
        self.assertEqual({c["id"] for c in chars if c["role"] == "hero"}, {"H_BUBBLES", "H_FLUFFY"})

    def test_group_is_not_villain(self):
        self.assertEqual(M["group_sheet"]["name"], "Bactro Gang")
        self.assertFalse(M["group_sheet"]["separate_villain"])

    def test_current_character_digests_when_imported(self):
        for c in M["characters"]:
            self.assertIsInstance(c["verified"], bool)
            if c["verified"]:
                self.assertTrue(c["current_master_path"])
                self.assertRegex(c["sha256"], r"^[0-9a-f]{64}$")
            else:
                self.assertIsNone(c["sha256"])

    def test_current_logo_digest_when_imported(self):
        logo = M["logo"]
        self.assertIsInstance(logo["verified"], bool)
        if logo["verified"]:
            self.assertRegex(logo["sha256"], r"^[0-9a-f]{64}$")
            self.assertTrue(logo["current_master_path"])
        else:
            self.assertIsNone(logo["sha256"])

    def test_unverified_release(self):
        self.assertIn(M["status"], {"WAITING_FOR_LOCAL_FILE_INGEST", "LOCAL_HASH_VERIFIED_AWAITING_GIT_PUSH", "APPROVED_RELEASE"})
        self.assertIsInstance(M["ico_package"]["verified"], bool)

if __name__ == "__main__":
    unittest.main()
