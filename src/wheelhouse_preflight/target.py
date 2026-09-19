"""Explicit target descriptions; never infer a remote target from the host."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from packaging.markers import default_environment
from packaging.tags import Tag, sys_tags
from packaging.version import InvalidVersion, Version

MARKER_KEYS = frozenset(
    {
        "implementation_name",
        "implementation_version",
        "os_name",
        "platform_machine",
        "platform_release",
        "platform_system",
        "platform_version",
        "python_full_version",
        "platform_python_implementation",
        "python_version",
        "sys_platform",
    }
)
MAX_TARGET_BYTES = 2 * 1024 * 1024
MAX_TAGS = 20_000
TAG_PATTERN = re.compile(r"^[A-Za-z0-9_]+-[A-Za-z0-9_]+-[A-Za-z0-9_]+$")


class InputError(ValueError):
    """An input cannot be interpreted safely or without guessing."""


@dataclass(frozen=True)
class Target:
    marker_environment: dict[str, str]
    compatible_tags: tuple[Tag, ...]

    @classmethod
    def from_dict(cls, data: Any) -> Target:
        if not isinstance(data, dict):
            raise InputError("Target must be a JSON object.")
        env = data.get("marker_environment")
        if not isinstance(env, dict):
            raise InputError("Target must contain marker_environment.")
        missing = sorted(MARKER_KEYS - env.keys())
        unknown = sorted(env.keys() - MARKER_KEYS)
        if missing or unknown:
            raise InputError(f"Target marker keys: missing={missing}, unknown={unknown}.")
        if any(not isinstance(v, str) or len(v) > 1024 for v in env.values()):
            raise InputError("Target marker values must be strings of at most 1024 characters.")
        try:
            python = Version(env["python_full_version"])
            Version(env["implementation_version"])
        except InvalidVersion as exc:
            raise InputError(
                "Target contains an invalid Python or implementation version."
            ) from exc
        if len(python.release) < 2 or env["python_version"] != ".".join(
            str(v) for v in python.release[:2]
        ):
            raise InputError("Target python_version must match python_full_version major.minor.")
        tags = data.get("compatible_tags")
        if not isinstance(tags, list) or not 0 < len(tags) <= MAX_TAGS:
            raise InputError(f"Target compatible_tags must contain 1..{MAX_TAGS} ordered tags.")
        parsed: list[Tag] = []
        for value in tags:
            if not isinstance(value, str) or len(value) > 200 or not TAG_PATTERN.fullmatch(value):
                raise InputError("Target tags must be expanded interpreter-abi-platform strings.")
            interpreter, abi, platform = value.split("-")
            parsed.append(Tag(interpreter, abi, platform))
        if len(set(parsed)) != len(parsed):
            raise InputError("Target compatible_tags must not contain duplicates.")
        return cls(dict(env), tuple(parsed))

    def to_dict(self) -> dict[str, Any]:
        return {
            "marker_environment": dict(self.marker_environment),
            "compatible_tags": [str(tag) for tag in self.compatible_tags],
        }


def capture_target() -> dict[str, Any]:
    """Capture on the deployment interpreter, or use a complete PEX platform file."""
    return {
        "marker_environment": dict(default_environment()),
        "compatible_tags": [str(tag) for tag in sys_tags()],
    }


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InputError(f"Duplicate target JSON key: {key}.")
        result[key] = value
    return result


def load_target(path: Path) -> Target:
    with path.open("rb") as stream:
        data = stream.read(MAX_TARGET_BYTES + 1)
    if len(data) > MAX_TARGET_BYTES:
        raise InputError("Target JSON exceeds the 2 MiB limit.")
    try:
        document = json.loads(data, object_pairs_hook=_unique_object)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise InputError(f"Invalid target JSON: {exc}") from exc
    return Target.from_dict(document)
