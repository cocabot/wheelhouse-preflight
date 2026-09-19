"""Command-line interface for checking an offline wheelhouse."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from . import __version__
from .audit import audit_wheelhouse
from .target import InputError, capture_target, load_target


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wheelhouse-preflight",
        description="Check wheels and their dependency closure for an explicit target.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("target", help="Print this interpreter's target manifest as JSON.")
    check = subparsers.add_parser(
        "check", help="Audit a wheelhouse without installing or downloading packages."
    )
    check.add_argument("path", type=Path, help="Directory containing wheel files.")
    check.add_argument(
        "--target",
        required=True,
        type=Path,
        help="JSON manifest captured on the intended target with the target command.",
    )
    check.add_argument(
        "--require",
        required=True,
        action="append",
        metavar="REQUIREMENT",
        help="Root requirement, e.g. 'app[extra]==1.2'; repeat for multiple roots.",
    )
    check.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def _safe_text(value: object) -> str:
    """Escape control characters in filenames, requirements, and diagnostics."""
    return json.dumps(str(value), ensure_ascii=True)[1:-1]


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True))


def _print_text(payload: dict[str, Any]) -> None:
    print(f"Wheelhouse preflight: {_safe_text(payload['status'])}")
    if "scope" in payload:
        print("Scope: " + _safe_text(payload["scope"]))
    roots = payload.get("roots", [])
    if roots:
        print("Requirements: " + ", ".join(_safe_text(root) for root in roots))
    if "selected" in payload:
        print(f"Selected distributions: {len(payload['selected'])}")
    for issue in payload.get("issues", []):
        severity = _safe_text(issue.get("severity", "error")).upper()
        code = _safe_text(issue["code"])
        print(f"{severity} [{code}]: {_safe_text(issue['message'])}")
        if issue.get("path"):
            print("  Dependency path: " + " -> ".join(map(_safe_text, issue["path"])))


def _invalid_input(exc: Exception) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "invalid_input",
        "issues": [
            {
                "code": "invalid_input",
                "message": str(exc),
                "path": [],
                "severity": "error",
                "package": None,
            }
        ],
    }


def _run(argv: Sequence[str] | None) -> int:
    args = _parser().parse_args(argv)
    output_format = "json" if args.command == "target" else args.format
    try:
        if args.command == "target":
            payload = capture_target()
            exit_code = 0
        else:
            target = load_target(args.target)
            report = audit_wheelhouse(args.path, args.require, target)
            payload = report.to_dict()
            exit_code = report.exit_code
    except (InputError, OSError, ValueError) as exc:
        payload = _invalid_input(exc)
        exit_code = 2
    if output_format == "json":
        _print_json(payload)
    else:
        _print_text(payload)
    return exit_code


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI, returning the exit status instead of terminating the caller."""
    try:
        exit_code = _run(argv)
        # Flush here so a consumer closing a pipe cannot cause a shutdown traceback.
        sys.stdout.flush()
        return exit_code
    except BrokenPipeError:
        try:
            sys.stdout.close()
        except OSError:
            pass
        return 0
