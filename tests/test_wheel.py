import struct
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from helpers import make_wheel

from wheelhouse_preflight.target import InputError
from wheelhouse_preflight.wheel import read_wheel


class WheelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def test_valid_identity(self):
        wheel = read_wheel(make_wheel(self.directory, name="Demo_Package"))
        self.assertEqual(wheel.name, "demo-package")

    def test_identity_mismatch(self):
        for field in ("Name: other", "Version: 2.0"):
            metadata = "Metadata-Version: 2.3\nName: demo\nVersion: 1.0\n"
            metadata = metadata.replace(
                "Name: demo" if field.startswith("Name") else "Version: 1.0", field
            )
            with self.subTest(field=field), self.assertRaises(InputError):
                read_wheel(make_wheel(self.directory, metadata=metadata))

    def test_duplicate_identity_header(self):
        with self.assertRaises(InputError):
            read_wheel(
                make_wheel(
                    self.directory,
                    metadata="Metadata-Version: 2.3\nName: demo\nName: demo\nVersion: 1.0\n",
                )
            )

    def test_invalid_requires_dist(self):
        with self.assertRaises(InputError):
            read_wheel(make_wheel(self.directory, dependencies=("not a requirement",)))

    def test_invalid_requires_python(self):
        with self.assertRaises(InputError):
            read_wheel(make_wheel(self.directory, python="not a specifier"))

    def test_zip_metadata_limit(self):
        path = make_wheel(self.directory)
        with (
            patch("wheelhouse_preflight.wheel.MAX_METADATA_BYTES", 20),
            self.assertRaises(InputError),
        ):
            read_wheel(path)

    def test_zip_duplicate_rejected(self):
        path = make_wheel(self.directory)
        with self.assertWarns(UserWarning), zipfile.ZipFile(path, "a") as archive:
            archive.writestr("demo-1.0.dist-info/METADATA", "bad")
        with self.assertRaises(InputError):
            read_wheel(path)

    def test_zip_paths_are_never_extracted(self):
        path = make_wheel(self.directory, extra_members={"../do-not-extract.txt": b"test"})
        read_wheel(path)
        self.assertFalse((self.directory.parent / "do-not-extract.txt").exists())

    def test_wheel_header_tags_must_agree(self):
        path = make_wheel(self.directory)
        renamed = path.with_name("demo-1.0-py2-none-any.whl")
        path.rename(renamed)
        with self.assertRaises(InputError):
            read_wheel(renamed)

    def test_missing_metadata(self):
        path = self.directory / "demo-1.0-py3-none-any.whl"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("payload.txt", "test")
        with self.assertRaises(InputError):
            read_wheel(path)

    def test_broken_deflate_becomes_a_diagnostic(self):
        path = make_wheel(self.directory)
        with zipfile.ZipFile(path) as archive:
            info = archive.getinfo("demo-1.0.dist-info/METADATA")
        raw = bytearray(path.read_bytes())
        filename_size, extra_size = struct.unpack_from("<HH", raw, info.header_offset + 26)
        raw[info.header_offset + 30 + filename_size + extra_size] = 0xFF
        path.write_bytes(raw)
        with self.assertRaises(InputError):
            read_wheel(path)

    def test_central_directory_limit_applies_before_zipfile_allocation(self):
        path = make_wheel(self.directory)
        with (
            patch("wheelhouse_preflight.wheel.MAX_CENTRAL_DIRECTORY_BYTES", 20),
            patch(
                "wheelhouse_preflight.wheel.zipfile.ZipFile",
                side_effect=AssertionError("must not allocate"),
            ),
            self.assertRaises(InputError),
        ):
            read_wheel(path)

    def test_compressed_tag_expansion_is_bounded(self):
        many = ".".join(f"x{i}" for i in range(8))
        path = make_wheel(self.directory, tag=f"{many}-{many}-{many}")
        with self.assertRaises(InputError):
            read_wheel(path)
