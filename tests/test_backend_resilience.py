import contextlib
import importlib
import io
import os
import sys
import unittest
from unittest import mock


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
PYTHON_DIR = os.path.join(ROOT, "python")
if PYTHON_DIR not in sys.path:
    sys.path.insert(0, PYTHON_DIR)


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
