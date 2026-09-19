"""Original, minimal wheel fixtures; these are tests, never adoption evidence."""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import zipfile
from pathlib import Path

from wheelhouse_preflight.target import Target


def target(system: str = "linux", python: str = "3.12.1") -> Target:
    windows = system == "win32"
    return Target.from_dict(
        {
            "marker_environment": {
                "implementation_name": "cpython",
                "implementation_version": python,
                "os_name": "nt" if windows else "posix",
                "platform_machine": "AMD64" if windows else "x86_64",
                "platform_release": "10" if windows else "6.8",
                "platform_system": "Windows" if windows else "Linux",
                "platform_version": "test",
                "python_full_version": python,
                "platform_python_implementation": "CPython",
                "python_version": ".".join(python.split(".")[:2]),
                "sys_platform": system,
            },
            "compatible_tags": [
                "cp312-cp312-win_amd64" if windows else "cp312-cp312-manylinux_2_17_x86_64",
                "py3-none-any",
            ],
        }
    )


def make_wheel(
    directory: Path,
    name: str = "demo",
    version: str = "1.0",
    *,
    dependencies: tuple[str, ...] = (),
    extras: tuple[str, ...] = (),
    python: str = ">=3.11",
    tag: str = "py3-none-any",
    build: str = "",
    metadata: str | None = None,
    extra_members: dict[str, bytes] | None = None,
) -> Path:
    normalized = name.replace("-", "_")
    stem = f"{normalized}-{version}"
    filename = f"{stem}{'-' + build if build else ''}-{tag}.whl"
    fields = [
        "Metadata-Version: 2.3",
        f"Name: {name}",
        f"Version: {version}",
        f"Requires-Python: {python}",
    ]
    fields += [f"Requires-Dist: {req}" for req in dependencies]
    fields += [f"Provides-Extra: {extra}" for extra in extras]
    entries = {
        f"{stem}.dist-info/METADATA": (
            metadata if metadata is not None else "\n".join(fields) + "\n\n"
        ).encode(),
        f"{stem}.dist-info/WHEEL": (
            "Wheel-Version: 1.0\nGenerator: wheelhouse-preflight-tests\n"
            f"Root-Is-Purelib: true\nTag: {tag}\n\n"
        ).encode(),
        f"{normalized}/__init__.py": (
            b'raise RuntimeError("A preflight audit must never import this package")\n'
        ),
        **(extra_members or {}),
    }
    record = io.StringIO(newline="")
    writer = csv.writer(record)
    for path, content in entries.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).rstrip(b"=").decode()
        writer.writerow([path, f"sha256={digest}", len(content)])
    writer.writerow([f"{stem}.dist-info/RECORD", "", ""])
    entries[f"{stem}.dist-info/RECORD"] = record.getvalue().encode()
    path = directory / filename
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for member, content in entries.items():
            archive.writestr(member, content)
    return path
