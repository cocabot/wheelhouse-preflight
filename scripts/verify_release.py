"""Verify an existing GitHub release before reusing its distributions on PyPI.

This is a maintainer release check, not an independent provenance guarantee.
Network requests and downloads happen separately in the read-only workflow job.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

REPOSITORY = "cocabot/wheelhouse-preflight"
VERSION = r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"


def validate_version(value: str) -> str:
    if re.fullmatch(VERSION, value) is None:
        raise ValueError("Version must be a stable X.Y.Z value, for example 0.1.0")
    return value


def verify_release(
    version: str,
    directory: Path,
    release: dict[str, Any],
    commit: dict[str, Any],
    runs: list[dict[str, Any]],
) -> dict[str, Any]:
    """Reject incomplete, mismatched, unvalidated, or changed release artifacts."""
    validate_version(version)
    tag = f"v{version}"
    url = f"https://github.com/{REPOSITORY}/releases/tag/{tag}"
    if (
        release.get("tag_name") != tag
        or release.get("html_url") != url
        or release.get("draft") is not False
        or release.get("prerelease") is not False
        or not release.get("published_at")
    ):
        raise ValueError("Expected the published stable release for the requested tag")
    sha = commit.get("sha", "")
    if not isinstance(sha, str) or re.fullmatch(r"[0-9a-f]{40}", sha) is None:
        raise ValueError("The release tag must resolve to a full commit SHA")
    if release.get("target_commitish") != sha:
        raise ValueError("The release target and current tag commit differ")
    successful_runs = [
        run
        for run in runs
        if run.get("head_sha") == sha
        and run.get("path") == ".github/workflows/release.yml"
        and run.get("status") == "completed"
        and run.get("conclusion") == "success"
        and run.get("event") in {"push", "workflow_dispatch"}
        and run.get("head_branch") in {"main", tag}
        and run.get("head_repository", {}).get("full_name") == REPOSITORY
    ]
    if not successful_runs:
        raise ValueError("No successful Release workflow exists for the exact tag commit")

    wheel = f"wheelhouse_preflight-{version}-py3-none-any.whl"
    sdist = f"wheelhouse_preflight-{version}.tar.gz"
    distributions = {wheel, sdist}
    expected = distributions | {"SHA256SUMS"}
    assets = release.get("assets", [])
    if len(assets) != len(expected) or {asset.get("name") for asset in assets} != expected:
        raise ValueError("Release must contain exactly the expected wheel, sdist, and SHA256SUMS")
    if {path.name for path in directory.iterdir()} != expected:
        raise ValueError("Downloaded files do not match the expected release asset names")

    checksums: dict[str, str] = {}
    for asset in assets:
        name = asset["name"]
        path = directory / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Release asset is not a regular file: {name}")
        if asset.get("state") != "uploaded" or path.stat().st_size != asset.get("size"):
            raise ValueError(f"Release asset is incomplete or has the wrong size: {name}")
        expected_url = f"https://github.com/{REPOSITORY}/releases/download/{tag}/{name}"
        if asset.get("browser_download_url") != expected_url:
            raise ValueError(f"Unexpected release asset download URL: {name}")
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if asset.get("digest") != f"sha256:{digest}":
            raise ValueError(f"Release API digest does not match downloaded bytes: {name}")
        checksums[name] = digest

    manifest: dict[str, str] = {}
    for line in (directory / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64}) [ *](\S+)", line)
        if match is None or match[2] not in distributions or match[2] in manifest:
            raise ValueError("SHA256SUMS contains an invalid, unexpected, or duplicate entry")
        manifest[match[2]] = match[1]
    if manifest != {name: checksums[name] for name in distributions}:
        raise ValueError("SHA256SUMS does not match both distribution files")
    return {
        "version": version,
        "release": url,
        "commit": sha,
        "release_workflow": successful_runs[0]["html_url"],
        "sha256": {name: checksums[name] for name in sorted(distributions)},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--release-json", type=Path, required=True)
    parser.add_argument("--commit-json", type=Path, required=True)
    parser.add_argument("--runs-json", type=Path, required=True)
    args = parser.parse_args()
    try:
        release = json.loads(args.release_json.read_text(encoding="utf-8"))
        commit = json.loads(args.commit_json.read_text(encoding="utf-8"))
        pages = json.loads(args.runs_json.read_text(encoding="utf-8"))
        runs = [run for page in pages for run in page["workflow_runs"]]
        result = verify_release(args.version, args.directory, release, commit, runs)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        parser.exit(1, f"Release verification failed: {error}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
