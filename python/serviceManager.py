#! python3
# Copyright (C) 2015 - 2016 Hong Jen Yee (PCMan) <pcman.tw@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

import os
import sys
import json
import importlib
import logging

logger = logging.getLogger(__name__)


def dir_path_to_import_path(dir_path: str, base_dir: str) -> str:
    """Converts a filesystem directory path to a Python package import path relative to base_dir.

    Raises ValueError if dir_path is not within base_dir.
    """
    abs_dir = os.path.abspath(dir_path)
    abs_base = os.path.abspath(base_dir)

    rel_path = os.path.relpath(abs_dir, abs_base)
    if rel_path.startswith("..") or os.path.isabs(rel_path):
        raise ValueError(f"Path {dir_path!r} is not within base directory {base_dir!r}")

    if rel_path == ".":
        return ""
    return rel_path.replace(os.sep, ".")


def ime_json_paths(module_dir: str) -> list:
    """Lists the language profile manifests of an input method module.

    Returns ime.json, followed by ime_profiles/*/ime.json. The files may not exist.
    """
    paths = [os.path.join(module_dir, "ime.json")]
    profiles_dir = os.path.join(module_dir, "ime_profiles")
    try:
        profiles = sorted(os.listdir(profiles_dir))
    except OSError:  # no ime_profiles dir
        return paths
    paths.extend(os.path.join(profiles_dir, profile, "ime.json") for profile in profiles)
    return paths


class TextServiceInfo:
    """Represents metadata and factory logic for a single PIME text service."""

    def __init__(self):
        """Initializes empty text service metadata."""
        self.name = ""
        self.moduleName = ""
        self.serviceName = ""
        self.guid = ""
        self.textServiceClass = None
        self.configTool = ""

    def loadFromJson(self, json_file: str, base_dir: str, module_dir: str = None):
        """Loads text service metadata from an ime.json configuration file.

        Args:
            json_file: Path to the service's ime.json file.
            base_dir: The base package directory on sys.path (e.g. the PIME 'python'
                directory) used to derive the Python package import path prefix for
                the text service module without hardcoded directory assumptions.
            module_dir: The IME module directory against which moduleName is
                resolved. Defaults to the directory of json_file.
        """
        dir_name = module_dir or os.path.dirname(json_file)
        package_path = dir_path_to_import_path(dir_name, base_dir)

        with open(json_file, encoding="UTF-8") as data_file:
            json_data = json.load(data_file)

        self.name = json_data.get("name", "")
        module_name = json_data["moduleName"]
        self.moduleName = f"{package_path}.{module_name}" if package_path else module_name

        self.serviceName = json_data["serviceName"]
        self.guid = json_data["guid"].lower()
        self.configTool = json_data.get("configTool", "")

    def createInstance(self, client):
        """Creates and returns an instance of the text service class for client.

        Lazily imports the service module and caches the class reference on first invocation.
        """
        if not self.textServiceClass:
            mod = importlib.import_module(self.moduleName)
            self.textServiceClass = getattr(mod, self.serviceName)
        return self.textServiceClass(client)


class TextServiceManager:
    """Manages discovery, registration, and creation of PIME text services."""

    def __init__(self):
        """Initializes an empty TextServiceManager."""
        self.services = {}

    def load(self, base_dir: str):
        """Loads and registers all input methods found in base_dir/input_methods.

        Args:
            base_dir: The base package directory on sys.path containing the
                'input_methods' package.
        """
        input_methods_dir = os.path.join(base_dir, "input_methods")
        for subdir in os.listdir(input_methods_dir):
            module_dir = os.path.join(input_methods_dir, subdir)
            for filename in ime_json_paths(module_dir):
                try:
                    info = TextServiceInfo()
                    info.loadFromJson(filename, base_dir, module_dir)
                except (FileNotFoundError, NotADirectoryError):
                    continue
                except Exception:
                    logger.exception("Failed to load text service from %s", filename)
                    continue
                if not info.guid:
                    continue
                # The first manifest of a GUID wins; skip duplicates.
                if info.guid in self.services:
                    logger.warning("Duplicate GUID %s in %s ignored", info.guid, filename)
                    continue
                self.services[info.guid] = info

    def createService(self, client, guid):
        """Creates an instance of the text service associated with the specified GUID."""
        guid = guid.lower()
        if guid in self.services:
            info = self.services[guid]
            return info.createInstance(client)
        return None
