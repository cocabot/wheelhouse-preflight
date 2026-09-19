# Release process

GitHub Releases is the initial distribution channel. This process produces a
Python wheel, source archive, and SHA-256 checksums. It does not publish to PyPI
and does not require a registry credential.

## Release gate

1. Resolve relevant defects and describe user-facing changes in `CHANGELOG.md`.
   Replace the candidate's `unreleased` heading with its intended release date
   as part of the reviewed release change; this entry alone is not proof of publication.
2. Set `__version__` in `src/wheelhouse_preflight/__init__.py`. Use Semantic
   Versioning; document changed CLI or JSON contracts and migrations explicitly.
   For a release through a PR, update `.github/release-version` to the same
   `X.Y.Z` value. Changing this file requests publication when the PR reaches `main`.
3. Open a focused PR with the problem, changes, validation, compatibility, and
   remaining limits. Review the diff and checks; do not describe an AI review as
   an independent human review.
4. Require the CI workflow to pass for the exact release commit. Inspect source
   and wheel build contents, install the built wheel in a clean environment,
   and run a representative audit. A green check on an older commit is insufficient.
5. Merge the reviewed PR with its `.github/release-version` change into `main`.
   The Release workflow reruns the full CI gate on the resulting commit, then
   creates `vX.Y.Z` and publishes artifacts for that exact commit. No separate
   release token or browser operation is needed; publication uses the workflow's
   built-in GitHub token. Ordinary pushes that do not change the version file
   do not request a release.
6. Inspect the resulting GitHub Release and attached artifacts. Record only the
   published release URL and actual validation results as release evidence.

Two alternative triggers are supported: pushing an annotated `vX.Y.Z` tag or
dispatching the Release workflow on `main` with a `version` input of `X.Y.Z`.
The version comes from `.github/release-version` for a `main` push, the tag name
for a tag push, or the supplied input for a manual dispatch. Other branch pushes
and manual dispatches from other branches cannot publish.

All triggers run the reusable CI workflow before granting the publication job
permission to write repository contents. The publication job checks that the
requested version matches the package version and a dated changelog entry.
It refuses an existing tag pointing to a different commit or an existing release.
Official actions are pinned to full commit SHAs. Review action updates rather
than blindly replacing pins.

The workflow creates the release as a draft, uploads artifacts and checksums,
then publishes it. A failure can leave a draft; inspect and finish or remove that
draft deliberately. Do not overwrite an existing public release or replace its
artifacts. Publish a new patch version for corrections.

## Local verification and optional tag trigger

```sh
python -m unittest discover -s tests -v
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m build
# Alternative to the version-file PR: tag an already validated release commit.
# Replace X.Y.Z with the actual package version.
git tag -a vX.Y.Z -m 'Release X.Y.Z'
git push origin vX.Y.Z
```

Do not tag the placeholder literally. Workflow permissions, protected tags, and
repository settings can block publication; report a blocked release instead of
claiming it happened. Initial bootstrap limitations must not be hidden in the
changelog or qualification evidence.

## Artifact verification

Download all release artifacts and `SHA256SUMS`. On systems with `sha256sum`:

```sh
sha256sum --check SHA256SUMS
python -m pip install ./wheelhouse_preflight-X.Y.Z-py3-none-any.whl
wheelhouse-preflight --version
```

The filename is a placeholder. Checksums detect changed bytes relative to the
published manifest; they do not independently establish publisher identity.

## Compatibility and maintenance

Patch releases preserve documented behavior except where a correctness or
security fix must reject an invalid input previously accepted. Explain such
changes clearly. Before 1.0, minor releases may change the public interface;
provide migration instructions when that happens.

Evaluate dependency and CI-action updates against real compatibility or security
needs and the declared supported range. There is no release-count target or
calendar-driven promise. External bug reports and verified regressions take
priority over cosmetic activity.
