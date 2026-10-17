import io
import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
PYTHON_DIR = os.path.join(ROOT, "python")
if PYTHON_DIR not in sys.path:
    sys.path.insert(0, PYTHON_DIR)


class CinbaseWildcardTests(unittest.TestCase):
    def setUp(self):
        from cinbase.cin import Cin
        self.cin = Cin(io.StringIO("{}"), "checj", True)

    def test_wildcard_double_asterisk_and_pua_no_crash(self):
        # Issue #627: pressing wildcard twice or matching PUA/big5Other caused KeyError/crash
        self.cin.chardefs = {
            "aa": ["\u4e00"],
            "bb": ["\ue000"],  # PUA character (index 7 in lowFrequencyCharSetList)
            "cc": ["\u9fa6"],  # big5Other
        }
        results = self.cin.getWildcardCharDefs("**", "*", 100)
        self.assertEqual(len(results), 3)
        self.assertIn("\u4e00", results)
        self.assertIn("\ue000", results)
        self.assertIn("\u9fa6", results)

    def test_wildcard_invalid_regex_handled(self):
        self.cin.chardefs = {"a": ["\u4e00"]}
        # Malformed pattern should safely return empty list instead of crashing
        results = self.cin.getWildcardCharDefs("[", "*", 100)
        self.assertIsInstance(results, list)


if __name__ == "__main__":
    unittest.main()
