import io
import json
import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
PYTHON_DIR = os.path.join(ROOT, "python")
if PYTHON_DIR not in sys.path:
    sys.path.insert(0, PYTHON_DIR)


class DayiSymbolTests(unittest.TestCase):
    def test_dsymbols_contains_equal_and_minus(self):
        # Issue #856: == and =- in Dayi caused stuck state
        dsymbols_path = os.path.join(PYTHON_DIR, "cinbase", "data", "dsymbols.json")
        with open(dsymbols_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        chardefs = data.get("chardefs", {})

        self.assertIn("=", chardefs)
        self.assertIn("＝", chardefs["="])
        self.assertIn("-", chardefs)
        self.assertIn("－", chardefs["-"])

    def test_dsymbols_class_resolves_equal_and_minus(self):
        from cinbase.dsymbols import dsymbols
        dsymbols_path = os.path.join(PYTHON_DIR, "cinbase", "data", "dsymbols.json")
        with open(dsymbols_path, "r", encoding="utf-8") as f:
            ds = dsymbols(f)

        self.assertTrue(ds.isInCharDef("="))
        self.assertIn("＝", ds.getCharDef("="))
        self.assertTrue(ds.isInCharDef("-"))
        self.assertIn("－", ds.getCharDef("-"))


if __name__ == "__main__":
    unittest.main()
