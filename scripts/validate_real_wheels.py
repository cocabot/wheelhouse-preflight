"""Check real Click/Colorama wheels on the CI host, including a missing wheel.

Download separately with pip; this script and the audit perform no network access.
This is maintainer validation, not independent adoption evidence.
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

from wheelhouse_preflight.audit import audit_wheelhouse
from wheelhouse_preflight.target import Target, capture_target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheelhouse", type=Path)
    args = parser.parse_args()
    target = Target.from_dict(capture_target())
    complete = audit_wheelhouse(args.wheelhouse, ["click==8.1.8", "colorama==0.4.6"], target)
    if complete.exit_code:
        raise SystemExit(json.dumps(complete.to_dict(), indent=2))
    click = next(item for item in complete.selected if item["name"] == "click")
    with tempfile.TemporaryDirectory() as temp:
        shutil.copyfile(args.wheelhouse / click["filename"], Path(temp) / click["filename"])
        incomplete = audit_wheelhouse(Path(temp), ["click==8.1.8"], target)
        expected = 1 if target.marker_environment["sys_platform"] == "win32" else 0
        if incomplete.exit_code != expected:
            raise SystemExit(json.dumps(incomplete.to_dict(), indent=2))
        if expected and not any(
            item.code == "missing_package" and item.package == "colorama"
            for item in incomplete.issues
        ):
            raise SystemExit("Missing the expected Colorama diagnostic on Windows")
    print(
        json.dumps(
            {
                "kind": "maintainer_validation",
                "target": target.marker_environment,
                "complete_status": complete.to_dict()["status"],
                "without_colorama_status": incomplete.to_dict()["status"],
                "artifacts": complete.selected,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
