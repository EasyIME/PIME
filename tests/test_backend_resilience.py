import contextlib
import importlib
import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
PYTHON_DIR = os.path.join(ROOT, "python")
if PYTHON_DIR not in sys.path:
    sys.path.insert(0, PYTHON_DIR)


class CinCountTests(unittest.TestCase):
    def make_cin(self, temp_dir, count_data):
        spec = importlib.util.spec_from_file_location("cin_module_for_test", os.path.join(PYTHON_DIR, "cinbase", "cin.py"))
        cin_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cin_module)
        Cin = cin_module.Cin

        cin = Cin.__new__(Cin)
        cin.keynames = {}
        cin.cincount = {}
        cin.chardefs = {}
        cin.privateuse = {}
        cin.dupchardefs = {}
        cin._count_dirty = False
        cin._last_count_save_time = 0.0
        cin.getCountFile = lambda name="cincount.json": os.path.join(temp_dir, name)
        with open(cin.getCountFile(), "w", encoding="utf-8") as f:
            json.dump(count_data, f)
        return cin

    def test_load_count_file_ignores_malformed_entries(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cin = self.make_cin(temp_dir, {
                "abc": {"A": 3},
                "bad": ["not", "a", "dict"],
                "also_bad": 2,
            })

            cin.loadCountFile()

            self.assertEqual(cin.cincount, {
                "abc": {"A": {"count": 3, "last": 0, "prev": {}}}
            })

    def test_add_and_sort_count_tolerate_bad_state(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cin = self.make_cin(temp_dir, {})
            cin.cincount = {"abc": "bad"}

            cin.addCount("abc", "A")
            cin.addCount(None, "B")

            self.assertEqual(cin.cincount["abc"]["A"]["count"], 1)
            self.assertEqual(cin.cincount["abc"]["A"]["prev"], {})
            self.assertEqual(cin.sortByCount("abc", ["B", "A"]), ["A", "B"])
            self.assertEqual(cin.sortByCount("missing", ["B", "A"]), ["B", "A"])

    def test_recent_and_context_scores_can_be_disabled_independently(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cin = self.make_cin(temp_dir, {
                "abc": {
                    "A": {"count": 1, "last": 100.0, "prev": {"文": 4}},
                    "B": {"count": 2, "last": 200.0, "prev": {}},
                }
            })
            cin.loadCountFile()

            with mock.patch("time.time", return_value=200.0):
                self.assertEqual(cin.sortByCount("abc", ["B", "A"], "文"), ["A", "B"])
                self.assertEqual(cin.sortByCount("abc", ["B", "A"], "文", useContext=False), ["B", "A"])

    def test_context_counts_are_capped(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cin = self.make_cin(temp_dir, {})

            for i in range(40):
                cin.addCount("abc", "A", "prev{0:02d}".format(i))

            prev = cin.cincount["abc"]["A"]["prev"]
            self.assertEqual(len(prev), cin.MAX_CONTEXT_ENTRIES)
            self.assertIn("prev39", prev)

    def test_save_count_file_is_throttled(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cin = self.make_cin(temp_dir, {})
            cin.cincount = {"abc": {"A": {"count": 1, "last": 0, "prev": {}}}}
            cin._count_dirty = True
            cin._last_count_save_time = 100.0

            with mock.patch("time.time", return_value=110.0):
                cin.saveCountFile()
            with open(cin.getCountFile(), "r", encoding="utf-8") as f:
                self.assertEqual(json.load(f), {})

            with mock.patch("time.time", return_value=111.0):
                cin.saveCountFile(force=True)
            with open(cin.getCountFile(), "r", encoding="utf-8") as f:
                self.assertEqual(json.load(f), cin.cincount)


class ServerResilienceTests(unittest.TestCase):
    def import_server(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return importlib.import_module("server")

    def input_then_eof(self, lines):
        iterator = iter(lines)

        def fake_input():
            try:
                return next(iterator)
            except StopIteration:
                raise EOFError

        return fake_input

    def test_server_continues_after_client_exception(self):
        server_mod = self.import_server()
        server = server_mod.Server()

        class FailingClient:
            def handleRequest(self, msg):
                raise RuntimeError("boom")

        server.clients["client-1"] = FailingClient()

        with mock.patch("builtins.input", side_effect=self.input_then_eof(['client-1|{"method":"onKeyDown"}'])), \
                mock.patch.object(server_mod, "append_error_log"), \
                contextlib.redirect_stdout(io.StringIO()) as stdout, \
                contextlib.redirect_stderr(io.StringIO()):
            server.run()

        self.assertIn('PIME_MSG|client-1|{"success":false}', stdout.getvalue())

    def test_server_ignores_malformed_request_line(self):
        server_mod = self.import_server()
        server = server_mod.Server()

        with mock.patch("builtins.input", side_effect=self.input_then_eof(["malformed-request"])), \
                mock.patch.object(server_mod, "append_error_log") as append_error_log, \
                contextlib.redirect_stdout(io.StringIO()) as stdout, \
                contextlib.redirect_stderr(io.StringIO()):
            server.run()

        self.assertEqual(stdout.getvalue(), "")
        append_error_log.assert_called_once()


if __name__ == "__main__":
    unittest.main()
