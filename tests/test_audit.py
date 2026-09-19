from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from helpers import make_wheel, target

from wheelhouse_preflight.audit import audit_wheelhouse
from wheelhouse_preflight.target import InputError


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def audit(self, roots=None, system="linux"):
        return audit_wheelhouse(self.directory, roots or ["demo==1.0"], target(system))

    def codes(self, report):
        return [issue.code for issue in report.issues]

    def test_transitive_closure_and_hashes(self):
        make_wheel(self.directory, dependencies=("child>=2",))
        make_wheel(self.directory, "child", "2.0", dependencies=("leaf",))
        make_wheel(self.directory, "leaf")
        report = self.audit()
        self.assertEqual(report.exit_code, 0)
        self.assertEqual([p["name"] for p in report.selected], ["child", "demo", "leaf"])
        self.assertTrue(all(len(p["sha256"]) == 64 for p in report.selected))
        self.assertEqual(json.loads(json.dumps(report.to_dict()))["status"], "ready")

    def test_reports_multiple_missing_dependencies_and_paths(self):
        make_wheel(self.directory, dependencies=("missing-a", "missing-b"))
        report = self.audit()
        self.assertEqual(self.codes(report), ["missing_package", "missing_package"])
        self.assertEqual(report.issues[1].path, ("demo==1.0", "missing-b"))

    def test_cross_platform_markers_never_use_host(self):
        make_wheel(self.directory, dependencies=('colorama; sys_platform == "win32"',))
        self.assertEqual(self.audit(system="linux").exit_code, 0)
        report = self.audit(system="win32")
        self.assertEqual(report.exit_code, 1)
        self.assertEqual(report.issues[0].package, "colorama")

    def test_extra_dependency(self):
        make_wheel(self.directory, extras=("speed",), dependencies=('fast; extra == "speed"',))
        self.assertEqual(self.audit().exit_code, 0)
        self.assertIn("missing_package", self.codes(self.audit(["demo[speed]"])))

    def test_extra_added_after_package_was_expanded(self):
        make_wheel(self.directory, dependencies=("child", "bridge"))
        make_wheel(
            self.directory, "child", extras=("feature",), dependencies=('leaf; extra == "feature"',)
        )
        make_wheel(self.directory, "bridge", dependencies=("child[feature]",))
        report = self.audit()
        self.assertIn("missing_package", self.codes(report))
        self.assertEqual(
            report.issues[0].path,
            ("demo==1.0", "bridge", "child[feature]", 'leaf; extra == "feature"'),
        )

    def test_cycle_terminates_and_late_constraint_is_checked(self):
        make_wheel(self.directory, dependencies=("child",))
        make_wheel(self.directory, "child", dependencies=("demo>=2",))
        report = self.audit()
        self.assertEqual(self.codes(report), ["version_mismatch"])

    def test_unknown_extra_does_not_pass(self):
        make_wheel(self.directory)
        self.assertEqual(self.codes(self.audit(["demo[typo]"])), ["unknown_extra"])

    def test_extra_normalization(self):
        make_wheel(
            self.directory,
            extras=("test_feature",),
            dependencies=('leaf; extra == "test-feature"',),
        )
        self.assertEqual(self.codes(self.audit(["demo[test.feature]"])), ["missing_package"])

    def test_python_constraint(self):
        make_wheel(self.directory, python=">=3.13")
        self.assertEqual(self.codes(self.audit()), ["requires_python"])

    def test_wheel_tag(self):
        make_wheel(self.directory, tag="cp312-cp312-win_amd64")
        self.assertEqual(self.codes(self.audit()), ["incompatible_wheel"])

    def test_preferred_wheel_metadata_is_used(self):
        make_wheel(self.directory, dependencies=("unneeded",))
        preferred = make_wheel(self.directory, tag="cp312-cp312-manylinux_2_17_x86_64")
        report = self.audit()
        self.assertEqual(report.exit_code, 0)
        self.assertEqual(report.selected[0]["filename"], preferred.name)

    def test_multiple_versions_are_explicitly_unsupported(self):
        make_wheel(self.directory)
        make_wheel(self.directory, version="2.0")
        report = self.audit()
        self.assertEqual(report.exit_code, 2)
        self.assertEqual(self.codes(report), ["ambiguous_versions"])

    def test_equally_ranked_builds_are_unsupported(self):
        make_wheel(self.directory, build="1")
        make_wheel(self.directory, build="2")
        self.assertEqual(self.codes(self.audit()), ["ambiguous_wheels"])

    def test_direct_url_not_resolved(self):
        make_wheel(self.directory, dependencies=("child @ https://example.invalid/child.whl",))
        self.assertEqual(self.codes(self.audit()), ["direct_url"])
        self.assertEqual(self.audit().exit_code, 2)

    def test_inactive_direct_url_does_not_fail(self):
        make_wheel(
            self.directory,
            dependencies=('child @ https://example.invalid/child.whl ; sys_platform == "win32"',),
        )
        self.assertEqual(self.audit().exit_code, 0)

    def test_versions_checked_for_every_root(self):
        make_wheel(self.directory)
        self.assertEqual(self.codes(self.audit(["demo==1.0", "demo>=2"])), ["version_mismatch"])

    def test_inactive_roots_do_not_report_ready(self):
        make_wheel(self.directory)
        self.assertEqual(
            self.codes(self.audit(['demo; sys_platform == "win32"'])), ["no_active_roots"]
        )

    def test_corrupt_wheel_is_reported_alongside_missing(self):
        (self.directory / "corrupt-1.0-py3-none-any.whl").write_bytes(b"not a ZIP")
        self.assertEqual(self.codes(self.audit()), ["invalid_wheel", "missing_package"])

    def test_unrelated_corrupt_wheel_prevents_ready(self):
        make_wheel(self.directory)
        (self.directory / "corrupt.whl").write_bytes(b"invalid")
        self.assertEqual(self.codes(self.audit()), ["invalid_wheel"])

    def test_sdist_does_not_satisfy_dependency(self):
        (self.directory / "demo-1.0.tar.gz").write_bytes(b"source is not executed")
        self.assertEqual(self.codes(self.audit()), ["missing_package"])

    def test_does_not_open_network_or_launch_process(self):
        make_wheel(self.directory)
        with (
            patch("socket.socket", side_effect=AssertionError("network")),
            patch("subprocess.Popen", side_effect=AssertionError("process")),
        ):
            self.assertEqual(self.audit().exit_code, 0)

    def test_invalid_root(self):
        with self.assertRaises(InputError):
            self.audit(["not a requirement"])

    def test_empty_root_set(self):
        with self.assertRaises(InputError):
            audit_wheelhouse(self.directory, [], target())

    def test_missing_directory(self):
        with self.assertRaises(InputError):
            audit_wheelhouse(self.directory / "missing", ["demo"], target())

    def test_empty_wheelhouse(self):
        self.assertEqual(self.codes(self.audit()), ["missing_package"])

    def test_symlink_is_not_read(self):
        real = make_wheel(self.directory)
        link = self.directory / "alias-1.0-py3-none-any.whl"
        try:
            link.symlink_to(real)
        except OSError:
            self.skipTest("Symlink permission unavailable")
        self.assertIn("invalid_wheel", self.codes(self.audit()))
