# Check a deployment wheelhouse in CI

Use wheelhouse-preflight after collecting your application's wheels and before
transferring or publishing the bundle. The check reads the existing files and
evaluates dependencies for your captured destination. It does not download,
install, or execute the packages in that bundle.

## Supply the destination and bundle

Capture the destination using the interpreter that will run the application:

```sh
python -m wheelhouse_preflight target > target.json
```

Run this on the destination or a faithful replica. A generic GitHub-hosted runner
does not describe your production machine merely because it has the same OS
name. For an offline destination, prepare the tool and its `packaging` dependency
on a connected machine first; see [offline installation](../README.md#install).
A PEX complete-platform file also works when it contains all supported marker
values and the ordered, expanded compatibility tags.

Before the check step, your existing build or artifact-download steps must place:

- The captured destination description at `deployment/target.json`.
- The application's `.whl` files in `deployment/wheelhouse/`.

These are example workspace paths. Change them to your build's actual output.
The directory must contain one version of each reachable distribution; several
platform wheels of that version are allowed. Keep the audit tool's installation
files separate from the application bundle.

Use your existing downloader, build process, or resolver to assemble the bundle.
The target JSON controls the audit; it does not change a preceding downloader's
behavior. In particular, do not assume `pip download --platform` alone evaluates
dependencies for a foreign environment. [pip's upstream discussion](https://github.com/pypa/pip/issues/11664)
explains the distinction, and [PEX supports complete target descriptions](https://docs.pex-tool.org/buildingpex.html#complete-platform)
for workflows that need cross-environment resolution.

## GitHub Actions gate

This is a **template**, not a claimed integration in another project. Save it in
your repository only after adding your bundle-preparation steps at the indicated
point. Replace the two paths and `my-application[postgres]==1.2.0` with your real
root requirement. The example application is a placeholder, not a published
package. Repeat `--require` when your deployment has several roots.

The template pins the published 0.1.0 tool and the same action revisions used by
this project's release validation. Python 3.11 runs the auditor; the captured
target determines the application's destination Python version.

```yaml
name: Deployment wheelhouse

on:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  preflight:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0
        with:
          python-version: '3.11'
      - name: Install the auditor
        run: >-
          python -m pip install
          "https://github.com/cocabot/wheelhouse-preflight/releases/download/v0.1.0/wheelhouse_preflight-0.1.0-py3-none-any.whl"

      # Insert your existing build/download steps here. They must provide
      # deployment/wheelhouse/*.whl and deployment/target.json in this workspace.
      # The template itself does not produce either input.

      - name: Check deployment dependencies
        shell: bash
        run: |
          python -m wheelhouse_preflight check deployment/wheelhouse \
            --target deployment/target.json \
            --require 'my-application[postgres]==1.2.0' \
            --format json > preflight.json
      - name: Retain the diagnostic report, including failures
        if: always()
        uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1
        with:
          name: wheelhouse-preflight-report
          path: preflight.json
          if-no-files-found: warn
```

Installing the auditor needs network access. The check itself reads local files.
The paths above are relative to the checked-out repository in the job workspace;
no container or filesystem mount is implied. If your preparation runs in a
container or another job, explicitly copy or download its outputs into this
workspace before checking them.

The check is the final command in its step. Its exit status therefore fails the
job when a defect (`1`) or invalid/unsupported input (`2`) is reported. Do not add
`continue-on-error`, `|| true`, or an unguarded later command that discards that
status. The upload step's `if: always()` retains diagnostics after a failed
check; a successful upload does not turn the failed check into a successful job.
If installation or argument parsing fails before a report can be written, the
artifact can be absent or empty: inspect the job log for that failure.

**Review report visibility before enabling uploads.** JSON reports contain the
captured target, package names and versions, filenames, dependency paths, and
artifact hashes; error messages may also contain local paths. For a proprietary
bundle, keep the report in an appropriately restricted workflow or remove the
upload step. Do not upload private wheels or target information to a public
workflow just to make a bug report.

A successful check establishes only supported metadata closure. Follow it with
installation and application startup tests on the destination. It does not check
native shared libraries, drivers, vulnerabilities, or package authenticity.

## See a real target-specific failure

The repository's [CI workflow](../.github/workflows/ci.yml) runs a real-wheel
example on native Linux, Windows, and macOS runners. From a reviewed checkout
with the tool installed, run:

```sh
python -m pip download --only-binary=:all: --no-deps \
  click==8.1.8 colorama==0.4.6 --dest demo-wheelhouse
python scripts/validate_real_wheels.py demo-wheelhouse > maintainer-validation.json
```

The first command downloads the example packages. The second captures the
current runner's environment and reads the wheels without installing or
executing them. It checks the complete bundle, then a temporary copy containing
only Click; your original directory is unchanged.

| Native environment | Complete bundle | Click without Colorama |
| --- | --- | --- |
| Windows | Pass | Missing Colorama reported |
| Linux or macOS | Pass | Pass: the Windows dependency marker does not apply |

These outcomes were observed in [the 0.1.0 release validation](https://github.com/cocabot/wheelhouse-preflight/actions/runs/35427951692).
The script's report records the native marker environment and selected artifact
hashes. A successful script means both expected outcomes matched; the deliberate
Windows failure is a test expectation, not a passing audit of that incomplete
bundle. No target is simulated by editing a platform field. These runs establish
maintainer validation, not external adoption or proof of production readiness.
