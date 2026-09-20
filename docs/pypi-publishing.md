# Publishing the existing release to PyPI

The initial release is available from [GitHub Releases](https://github.com/cocabot/wheelhouse-preflight/releases/tag/v0.1.0).
Adding this workflow does not publish a package or configure a PyPI account.
PyPI publication remains pending until the owner sets up the publisher and a
publication run succeeds. Do not advertise a PyPI install command before then.

The workflow republishes the **same wheel and source archive** from a successful
GitHub release. It does not rebuild them or require a new package version.

## One-time account setup by the owner

The account owner must sign in to PyPI and handle account verification, two-factor
authentication, and any terms personally. Do not share passwords, recovery codes,
API tokens, or other credentials in GitHub, issues, or chat.

For a project that does not yet exist, open PyPI's
[account publishing page](https://pypi.org/manage/account/publishing/) and add a
pending GitHub publisher with these exact values:

| Field | Value |
| --- | --- |
| PyPI project name | `wheelhouse-preflight` |
| Repository owner | `cocabot` |
| Repository name | `wheelhouse-preflight` |
| Workflow filename | `publish-pypi.yml` |
| Environment name | `pypi` |

Use the workflow **filename**, without `.github/workflows/`. If the project
already exists and belongs to you, add the publisher under that project's
Publishing settings instead. A pending publisher does not reserve the name;
if another account owns it, resolve that conflict before publishing.

The owner should also configure the GitHub
[`pypi` environment](https://github.com/cocabot/wheelhouse-preflight/settings/environments)
to allow deployments from `main` only, with any required reviewer protection the
owner wants. The workflow itself also rejects all branches other than `main`.
No repository secret or long-lived PyPI token is needed.

The setup follows PyPI's official instructions for
[creating a project through a pending publisher](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/)
and [publishing with a Trusted Publisher](https://docs.pypi.org/trusted-publishers/using-a-publisher/).

## Request publication after setup

Use [Actions → Publish existing release to PyPI](https://github.com/cocabot/wheelhouse-preflight/actions/workflows/publish-pypi.yml),
choose `main`, enter `0.1.0` as the version, and enable the **publish** checkbox.
Leaving **publish** disabled runs the complete preparation and smoke tests
without contacting PyPI for an upload or requesting a publishing credential.
This dry run works before the pending publisher is configured.
Alternatively, a reviewed change
can create or update `.github/pypi-version` to the intended `X.Y.Z` version;
merging that file change to `main` requests publication. This marker is deliberately
absent until the publisher is configured. Ordinary documentation and code changes
do not trigger PyPI publication.

The preparation job has read-only GitHub permissions and no OIDC publishing
permission. It checks:

- Stable `X.Y.Z` input and a published, non-prerelease `vX.Y.Z` GitHub release.
- The current tag commit matches the release target, and the Release workflow
  succeeded for that exact commit in this repository.
- The wheel, source archive, and checksum manifest have the expected names.
  Downloaded byte sizes and SHA-256 digests match GitHub's asset records, and the
  two distributions match `SHA256SUMS` without extra or duplicate entries.
- Strict Twine metadata checks and a clean wheel installation with CLI version
  and target-manifest smoke tests. The checksums are rechecked after installation.

Only the two verified distributions pass to the separate publishing job through
an immutable workflow artifact. That job downloads this exact artifact, checks
out no source, runs no package code, and uses the pinned PyPA publishing action
with `id-token: write`. PyPI exchanges the workflow identity for a short-lived
upload credential. Publication attestations are enabled. Other jobs cannot
request that publishing credential.

Checksums and a successful workflow show consistency with the GitHub release;
they do not independently prove authorship or rule out a compromised maintainer
account. Review release and workflow changes before merging them.

## Confirm the result

After the publishing job succeeds, check the
[PyPI project](https://pypi.org/project/wheelhouse-preflight/) and version files.
Their filenames and SHA-256 digests must match the existing GitHub release.
In a fresh environment, install the exact published version and run
`wheelhouse-preflight --version` and `wheelhouse-preflight target`.
Record the actual project and workflow URLs in the evidence record. Maintainer
verification downloads are not evidence of independent user adoption.

If identity verification fails, compare the owner, repository, workflow filename,
and environment with the fields above. A blocked or failed run is not publication.
If some files uploaded before a failure, inspect PyPI's existing files and hashes
before retrying; the workflow intentionally does not silently skip existing files.
Do not delete or replace public release artifacts to force a retry, and do not
create an otherwise meaningless version simply to increase release counts.
