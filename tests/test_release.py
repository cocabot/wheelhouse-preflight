"""Prevent publishing mismatched or unvalidated GitHub release assets to PyPI."""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts.verify_release import REPOSITORY, validate_version, verify_release


class ReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.directory = Path(temp.name)
        self.wheel = "wheelhouse_preflight-0.1.0-py3-none-any.whl"
        self.sdist = "wheelhouse_preflight-0.1.0.tar.gz"
        files = {self.wheel: b"wheel bytes", self.sdist: b"source archive bytes"}
        manifest = "".join(
            f"{hashlib.sha256(data).hexdigest()}  {name}\n" for name, data in files.items()
        )
        files["SHA256SUMS"] = manifest.encode()
        self.assets = []
        for name, data in files.items():
            (self.directory / name).write_bytes(data)
            self.assets.append(
                {
                    "name": name,
                    "state": "uploaded",
                    "size": len(data),
                    "digest": f"sha256:{hashlib.sha256(data).hexdigest()}",
                    "browser_download_url": (
                        f"https://github.com/{REPOSITORY}/releases/download/v0.1.0/{name}"
                    ),
                }
            )
        self.sha = "a" * 40
        self.release = {
            "tag_name": "v0.1.0",
            "html_url": f"https://github.com/{REPOSITORY}/releases/tag/v0.1.0",
            "draft": False,
            "prerelease": False,
            "published_at": "2026-09-19T06:56:57Z",
            "target_commitish": self.sha,
            "assets": self.assets,
        }
        self.commit = {"sha": self.sha}
        self.run = {
            "head_sha": self.sha,
            "path": ".github/workflows/release.yml",
            "status": "completed",
            "conclusion": "success",
            "event": "push",
            "head_branch": "main",
            "head_repository": {"full_name": REPOSITORY},
            "html_url": f"https://github.com/{REPOSITORY}/actions/runs/123",
        }

    def verify(self) -> dict:
        return verify_release("0.1.0", self.directory, self.release, self.commit, [self.run])

    def test_accepts_identical_bytes_and_successful_release_for_exact_commit(self) -> None:
        result = self.verify()
        self.assertEqual(result["commit"], self.sha)
        self.assertEqual(result["release_workflow"], self.run["html_url"])
        self.assertEqual(set(result["sha256"]), {self.wheel, self.sdist})

    def test_rejects_invalid_versions_and_unpublished_or_retargeted_releases(self) -> None:
        for version in ("v0.1.0", "0.1.0rc1", "01.0.0", "0.1.0\n", "../0.1.0"):
            with self.subTest(version=version), self.assertRaises(ValueError):
                validate_version(version)
        for field, value in (
            ("draft", True),
            ("prerelease", True),
            ("published_at", None),
            ("tag_name", "v0.2.0"),
            ("target_commitish", "b" * 40),
        ):
            with self.subTest(field=field):
                release = {**self.release, field: value}
                with self.assertRaises(ValueError):
                    verify_release("0.1.0", self.directory, release, self.commit, [self.run])

    def test_rejects_stale_failed_or_untrusted_release_runs(self) -> None:
        for field, value in (
            ("head_sha", "b" * 40),
            ("conclusion", "failure"),
            ("status", "in_progress"),
            ("path", ".github/workflows/ci.yml"),
            ("event", "pull_request"),
            ("head_branch", "feature"),
            ("head_repository", {"full_name": "someone/another-repository"}),
        ):
            with self.subTest(field=field), self.assertRaises(ValueError):
                verify_release(
                    "0.1.0", self.directory, self.release, self.commit, [{**self.run, field: value}]
                )

    def test_detects_same_size_changed_bytes_and_extra_downloaded_files(self) -> None:
        wheel = self.directory / self.wheel
        original = wheel.read_bytes()
        wheel.write_bytes(b"X" * len(original))
        with self.assertRaisesRegex(ValueError, "digest"):
            self.verify()
        wheel.write_bytes(original)
        (self.directory / "unexpected.whl").write_bytes(b"extra")
        with self.assertRaisesRegex(ValueError, "asset names"):
            self.verify()

    def test_checks_manifest_even_when_asset_api_digests_match(self) -> None:
        path = self.directory / "SHA256SUMS"
        valid = path.read_text()
        for manifest in (
            valid + valid.splitlines()[0] + "\n",
            valid.replace(self.wheel, "../outside.whl"),
            valid.splitlines()[0] + "\n",
            valid.replace(hashlib.sha256(b"wheel bytes").hexdigest(), "0" * 64),
        ):
            with self.subTest(manifest=manifest):
                path.write_text(manifest)
                self.assets[-1]["size"] = path.stat().st_size
                self.assets[-1]["digest"] = (
                    f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"
                )
                with self.assertRaisesRegex(ValueError, "SHA256SUMS"):
                    self.verify()

    def test_requires_exact_asset_set_and_uploaded_state(self) -> None:
        self.assets[0]["state"] = "new"
        with self.assertRaisesRegex(ValueError, "incomplete"):
            self.verify()
        self.assets[0]["state"] = "uploaded"
        self.assets.append(self.assets[0])
        with self.assertRaisesRegex(ValueError, "exactly"):
            self.verify()
