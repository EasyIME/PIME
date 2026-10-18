import os
import sys
import json
import shutil
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
PYTHON_DIR = os.path.join(ROOT, "python")
if PYTHON_DIR not in sys.path:
    sys.path.insert(0, PYTHON_DIR)

from serviceManager import TextServiceManager, TextServiceInfo, dir_path_to_import_path
from server import Server, Client


class ServiceManagerTests(unittest.TestCase):
    def setUp(self):
        self.test_root = os.path.join(ROOT, "scratch", f"test_im_dir_{os.getpid()}")
        os.makedirs(self.test_root, exist_ok=True)
        sys.path.insert(0, self.test_root)
        self._saved_modules = {
            k: v for k, v in sys.modules.items()
            if k == "input_methods" or k.startswith("input_methods.")
        }
        for k in self._saved_modules:
            del sys.modules[k]

    def tearDown(self):
        if self.test_root in sys.path:
            sys.path.remove(self.test_root)
        for k in list(sys.modules.keys()):
            if k == "input_methods" or k.startswith("input_methods."):
                del sys.modules[k]
        sys.modules.update(self._saved_modules)
        shutil.rmtree(self.test_root, ignore_errors=True)

    def _create_dummy_ime(self, subdir_name, guid, module_name="my_ime", class_name="MyService"):
        pkg_dir = os.path.join(self.test_root, "input_methods")
        os.makedirs(pkg_dir, exist_ok=True)
        init_file = os.path.join(pkg_dir, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w", encoding="utf-8") as f:
                pass

        im_dir = os.path.join(pkg_dir, subdir_name)
        os.makedirs(im_dir, exist_ok=True)
        ime_json = os.path.join(im_dir, "ime.json")
        with open(ime_json, "w", encoding="utf-8") as f:
            json.dump({
                "name": "Test IME",
                "moduleName": module_name,
                "serviceName": class_name,
                "guid": guid,
            }, f)
        py_file = os.path.join(im_dir, f"{module_name}.py")
        with open(py_file, "w", encoding="utf-8") as f:
            f.write(f"""class {class_name}:
    def __init__(self, client):
        self.client = client
""")
        return im_dir

    def test_init_is_empty(self):
        mgr = TextServiceManager()
        self.assertEqual(mgr.services, {})

    def test_load_nonexistent_directory_raises_oserror(self):
        mgr = TextServiceManager()
        with self.assertRaises(OSError):
            mgr.load(os.path.join(self.test_root, "nonexistent"))

    def test_load_from_directory_registers_services(self):
        guid = "{11111111-2222-3333-4444-555555555555}"
        self._create_dummy_ime("dummy1", guid)

        mgr = TextServiceManager()
        mgr.load(self.test_root)

        self.assertIn(guid.lower(), mgr.services)
        self.assertEqual(mgr.services[guid.lower()].name, "Test IME")

    def test_load_from_json_with_explicit_base_dir(self):
        guid = "{33333333-4444-5555-6666-777777777777}"
        im_dir = self._create_dummy_ime("dummy_explicit", guid, module_name="exp_mod", class_name="ExpClass")
        json_file = os.path.join(im_dir, "ime.json")

        info = TextServiceInfo()
        info.loadFromJson(json_file, self.test_root)

        self.assertEqual(info.moduleName, "input_methods.dummy_explicit.exp_mod")
        self.assertEqual(info.guid, guid.lower())

    def test_create_service_instance(self):
        guid = "{12345678-abcd-ef01-2345-6789abcdef01}"
        self._create_dummy_ime("dummy3", guid, module_name="test_mod", class_name="TestClass")

        mgr = TextServiceManager()
        mgr.load(self.test_root)
        service = mgr.createService("dummy_client", guid)

        self.assertIsNotNone(service)
        self.assertEqual(service.client, "dummy_client")

    def test_create_service_unknown_guid_returns_none(self):
        mgr = TextServiceManager()
        self.assertIsNone(mgr.createService(None, "{00000000-0000-0000-0000-000000000000}"))

    def test_server_delegates_to_service_manager(self):
        guid = "{fedcba98-7654-3210-fedc-ba9876543210}"
        self._create_dummy_ime("dummy4", guid, module_name="srv_mod", class_name="SrvClass")

        server = Server(self.test_root)

        client = Client(server)
        success = client.init({
            "id": guid,
            "isWindows8Above": True,
            "isMetroApp": False,
            "isUiLess": False,
            "isConsole": False,
        })

        self.assertTrue(success)
        self.assertIsNotNone(client.service)
        self.assertEqual(client.service.client, client)

    def test_dir_path_to_import_path_conversions(self):
        base = os.path.join(self.test_root, "base")
        sub_dir = os.path.join(base, "pkg", "subpkg")
        top_pkg = os.path.join(base, "pkg")

        test_cases = [
            ("sub_dir", sub_dir, "pkg.subpkg"),
            ("top_pkg", top_pkg, "pkg"),
            ("base_dir", base, ""),
        ]

        for name, path, expected in test_cases:
            with self.subTest(case=name, path=path):
                self.assertEqual(dir_path_to_import_path(path, base), expected)

    def test_dir_path_to_import_path_outside_base_raises(self):
        base = os.path.join(self.test_root, "base")
        outside = os.path.join(self.test_root, "outside")

        with self.assertRaises(ValueError):
            dir_path_to_import_path(outside, base)


if __name__ == "__main__":
    unittest.main()
