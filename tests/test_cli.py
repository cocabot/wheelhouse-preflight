"""CLI contracts: explicit targets, machine-readable errors, and safe terminals."""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

from wheelhouse_preflight import cli
from wheelhouse_preflight.target import InputError


class CliTests(unittest.TestCase):
    def invoke(self, args: list[str]) -> tuple[int, str]:
        output = io.StringIO()
        with redirect_stdout(output):
            status = cli.main(args)
        return status, output.getvalue()

    def test_target_outputs_manifest_as_json(self) -> None:
        manifest = {
            "schema_version": 1,
            "marker_environment": {},
            "tags": ["py3-none-any"],
        }
        with patch.object(cli, "capture_target", return_value=manifest):
            status, output = self.invoke(["target"])
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(output), manifest)

    def test_check_uses_explicit_target_and_repeated_roots(self) -> None:
        target = object()
        payload = {"schema_version": 1, "status": "pass", "selected": [], "issues": []}
        report = Mock(exit_code=0)
        report.to_dict.return_value = payload
        with (
            patch.object(cli, "load_target", return_value=target) as load,
            patch.object(cli, "audit_wheelhouse", return_value=report) as audit,
        ):
            status, output = self.invoke(
                [
                    "check",
                    "wheelhouse",
                    "--target",
                    "linux.json",
                    "--require",
                    "app[extra]==1.2",
                    "--require",
                    "helper==2",
                    "--format",
                    "json",
                ]
            )
        load.assert_called_once_with(Path("linux.json"))
        audit.assert_called_once_with(Path("wheelhouse"), ["app[extra]==1.2", "helper==2"], target)
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(output), payload)

    def test_check_preserves_audit_failure_status(self) -> None:
        report = Mock(exit_code=1)
        report.to_dict.return_value = {
            "status": "fail",
            "issues": [{"code": "missing", "message": "Missing wheel"}],
        }
        with (
            patch.object(cli, "load_target"),
            patch.object(cli, "audit_wheelhouse", return_value=report),
        ):
            status, output = self.invoke(
                ["check", ".", "--target", "target.json", "--require", "app==1"]
            )
        self.assertEqual(status, 1)
        self.assertIn("Missing wheel", output)

    def test_input_errors_are_json_with_exit_two(self) -> None:
        for error in (
            InputError("bad manifest"),
            FileNotFoundError("missing file"),
            ValueError("bad value"),
        ):
            with self.subTest(error=type(error).__name__):
                with patch.object(cli, "load_target", side_effect=error):
                    status, output = self.invoke(
                        [
                            "check",
                            ".",
                            "--target",
                            "broken.json",
                            "--require",
                            "app==1",
                            "--format",
                            "json",
                        ]
                    )
                payload = json.loads(output)
                self.assertEqual(status, 2)
                self.assertEqual(payload["schema_version"], 1)
                self.assertEqual(payload["status"], "invalid_input")
                self.assertEqual(payload["issues"][0]["message"], str(error))

    def test_target_capture_error_is_also_json(self) -> None:
        with patch.object(cli, "capture_target", side_effect=InputError("unsupported target")):
            status, output = self.invoke(["target"])
        self.assertEqual(status, 2)
        self.assertEqual(json.loads(output)["status"], "invalid_input")

    def test_text_escapes_untrusted_terminal_control_characters(self) -> None:
        report = Mock(exit_code=1)
        report.to_dict.return_value = {
            "status": "fail",
            "roots": ["app\x1b[2J"],
            "issues": [
                {
                    "code": "bad_wheel",
                    "severity": "error",
                    "message": "evil\rfilename\x1b[31m",
                    "path": ["app==1", "bad\npackage"],
                }
            ],
        }
        with (
            patch.object(cli, "load_target"),
            patch.object(cli, "audit_wheelhouse", return_value=report),
        ):
            status, output = self.invoke(
                ["check", ".", "--target", "target.json", "--require", "app==1"]
            )
        self.assertEqual(status, 1)
        self.assertNotIn("\x1b", output)
        self.assertNotIn("\r", output)
        self.assertIn(r"bad\npackage", output)
        self.assertIn(r"\u001b", output)

    def test_explicit_target_and_roots_are_required(self) -> None:
        for args in (
            ["check", ".", "--require", "app==1"],
            ["check", ".", "--target", "t.json"],
        ):
            with self.subTest(args=args), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    cli.main(args)
                self.assertEqual(raised.exception.code, 2)

    def test_broken_output_pipe_exits_cleanly(self) -> None:
        output = Mock()
        output.write.side_effect = BrokenPipeError()
        with (
            patch.object(cli, "capture_target", return_value={}),
            patch("sys.stdout", output),
        ):
            status = cli.main(["target"])
        self.assertEqual(status, 0)
        output.close.assert_called_once()

    def test_broken_pipe_during_flush_exits_cleanly(self) -> None:
        output = Mock()
        output.flush.side_effect = BrokenPipeError()
        with (
            patch.object(cli, "capture_target", return_value={}),
            patch("sys.stdout", output),
        ):
            status = cli.main(["target"])
        self.assertEqual(status, 0)
        output.close.assert_called_once()
