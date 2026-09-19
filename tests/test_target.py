import json
import tempfile
import unittest
from pathlib import Path

from helpers import target

from wheelhouse_preflight.target import InputError, Target, capture_target, load_target


class TargetTests(unittest.TestCase):
    def test_capture_roundtrip(self):
        data = capture_target()
        self.assertEqual(Target.from_dict(data).to_dict(), data)

    def test_missing_environment_field_refuses_host_fallback(self):
        data = target().to_dict()
        del data["marker_environment"]["platform_release"]
        with self.assertRaises(InputError):
            Target.from_dict(data)

    def test_inconsistent_python_version(self):
        data = target().to_dict()
        data["marker_environment"]["python_version"] = "3.11"
        with self.assertRaises(InputError):
            Target.from_dict(data)

    def test_invalid_tags(self):
        for tags in ([], ["py3"], ["py2.py3-none-any"], ["py3-none-any", "py3-none-any"], [False]):
            with self.subTest(tags=tags), self.assertRaises(InputError):
                Target.from_dict({**target().to_dict(), "compatible_tags": tags})

    def test_non_string_values(self):
        data = target().to_dict()
        data["marker_environment"]["os_name"] = 123
        with self.assertRaises(InputError):
            Target.from_dict(data)

    def test_file_roundtrip_and_duplicate_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "target.json"
            path.write_text(json.dumps(target().to_dict()), encoding="utf-8")
            self.assertEqual(load_target(path), target())
            path.write_text('{"marker_environment":{},"marker_environment":{}}', encoding="utf-8")
            with self.assertRaises(InputError):
                load_target(path)

    def test_oversized_target(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "target.json"
            path.write_bytes(b" " * (2 * 1024 * 1024 + 1))
            with self.assertRaises(InputError):
                load_target(path)
