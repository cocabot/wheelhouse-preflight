# wheelhouse-preflight

Check whether a local Python wheel bundle contains the dependencies required by
an explicit deployment target, **before transferring it to an offline machine**.

For release and platform engineers assembling air-gapped deployments, this CLI
finds missing dependencies, target-specific marker mistakes, incompatible wheels,
and Python-version constraints by reading wheel metadata. It does not install,
import, execute, or download the packages being checked.

## Why this exists

A wheel collection that looks complete on a Linux build machine can miss a
dependency needed on Windows or another Python version. Wheel-selection flags
alone do not describe every dependency marker. Upstream reports such as
[pip #13442](https://github.com/pypa/pip/issues/13442) and
[pip #11664](https://github.com/pypa/pip/issues/11664) describe this failure mode.

wheelhouse-preflight accepts a captured target environment and checks an already
assembled, single-version wheelhouse. It provides dependency paths and JSON
findings suitable for a CI gate. It complements your downloader and deployment
tests; it is not a resolver or installer. See the
[research and alternatives](docs/research.md) for the evidence and scope.

## Install

Python 3.11 or newer is required to run the tool.

Install the published 0.1.0 wheel in a virtual environment:

```sh
python -m venv .venv
# POSIX shell; on Windows use .venv\\Scripts\\activate
. .venv/bin/activate
python -m pip install "https://github.com/cocabot/wheelhouse-preflight/releases/download/v0.1.0/wheelhouse_preflight-0.1.0-py3-none-any.whl"
wheelhouse-preflight --help
```

This command needs network access and installs the `packaging` dependency.
[Release v0.1.0](https://github.com/cocabot/wheelhouse-preflight/releases/tag/v0.1.0)
also provides a source archive and SHA256SUMS. The wheel's SHA-256 is
`bf77097054c777d6526fbc604dbe035c17aac28ea1d9eccf6ec331736ee616ca`.
A checksum detects differing bytes; it does not independently authenticate the publisher.

To work from source instead:

```sh
git clone https://github.com/cocabot/wheelhouse-preflight.git
cd wheelhouse-preflight
python -m venv .venv
# POSIX shell; on Windows use .venv\Scripts\activate
. .venv/bin/activate
python -m pip install .
wheelhouse-preflight --help
```

For reproducible use, check out a reviewed commit or release tag before
installing. Check [GitHub Releases](https://github.com/cocabot/wheelhouse-preflight/releases)
for available built wheels and source archives. A PyPI publication is not assumed
by these instructions.

For offline installation of this tool, prepare its wheel and the `packaging`
dependency on a connected machine, transfer those files, then install using
`python -m pip install --no-index --find-links TOOL_WHEELS wheelhouse-preflight`.
Use a separate directory from the application wheelhouse being audited.

## Try it with real wheels

From the cloned repository, download two pinned packages used as a compatibility
example. This download requires network access; the following audit does not.
Neither downloaded package is installed or executed by this example.

```sh
python -m pip download --only-binary=:all: --no-deps \
  click==8.1.8 colorama==0.4.6 --dest demo-wheelhouse
wheelhouse-preflight target > target.json
wheelhouse-preflight check demo-wheelhouse \
  --target target.json --require 'click==8.1.8' --format json
```

This captures your **current interpreter**, so it is a local demonstration.
Click's metadata requires Colorama on Windows. The validation script checks the
complete bundle, then checks a temporary copy containing only Click: omission
must fail on Windows and pass on the other platforms in the CI matrix.

```sh
python scripts/validate_real_wheels.py demo-wheelhouse
```

The script reports the target, selected artifact hashes, and observed outcomes.
It does not modify the original directory. These are maintainer compatibility
checks, not evidence that Click or Colorama users have adopted this tool.

## Quick start

**1. Capture the destination, using the interpreter that will run the application.**

Install this tool in that environment, then run:

```sh
python -m wheelhouse_preflight target > target.json
```

Transfer `target.json` back to the machine holding your wheels. This captures
the full marker environment and ordered wheel tags; it must describe the
destination, not merely the machine downloading the packages. A faithful replica
of the destination can also be used. A PEX complete-platform file with all
supported marker keys and expanded tags uses the same input shape.

**2. Audit the collected wheels and your actual root requirements.**

```sh
# Replace my-application with a distribution present in your wheelhouse.
wheelhouse-preflight check ./wheelhouse \
  --target target.json \
  --require 'my-application[postgres]==1.2.0'
```

Repeat `--require` for multiple roots. Requested extras and applicable transitive
requirements are followed. The wheelhouse should have one version of each
reachable distribution; different platform wheels of that same version are
allowed. This tool does not backtrack through alternative package versions.

```sh
wheelhouse-preflight check ./wheelhouse \
  --target target.json \
  --require 'my-application==1.2.0' \
  --require 'my-plugin>=2,<3' \
  --format json > preflight.json
```

The example application names above are placeholders, not published packages or
claims of adoption. `python -m wheelhouse_preflight` exposes the same interface
as the console command.

**3. Treat the result as a metadata check, then test installation and startup on
the destination.**

| Exit status | Meaning | Next action |
| --- | --- | --- |
| `0` | The supported metadata checks found no closure problem. | Continue to deployment tests. |
| `1` | A defect was found in the bundle for the requested target. | Inspect findings and repair the bundle. |
| `2` | Input is invalid or the requested audit is unsupported. | Correct the input or use a resolver for the unsupported case. |

Keep the exit status when integrating with CI. JSON results include a
`schema_version`; findings contain codes, messages, and dependency paths. The
initial schema and CLI may change before version 1.0; consult the changelog when
upgrading and pin the version used by automation.

## Use it in your deployment pipeline

The [CI integration guide](docs/ci-integration.md) provides a GitHub Actions
gate for your existing wheelhouse, including failure-report retention and
target-capture instructions. It also explains the native Windows/Linux/macOS
Click example so you can evaluate the tool before connecting your own bundle.

## What is checked

- Root and transitive `Requires-Dist` requirements, version constraints, and extras.
- Environment markers evaluated against the explicit destination description.
- Wheel filename compatibility tags against the destination's ordered tags.
- `Requires-Python` against the destination Python version.
- Missing, malformed, and ambiguous distributions, with diagnostic paths.

The tool reads local `.whl` files directly. Source distributions, editable
projects, VCS references, and direct-URL dependencies are not resolved or built.
Use your package manager or PEX to resolve a bundle with multiple package
versions before auditing it. This tool does not read requirements files, lockfiles,
or package indexes.

## Limits that matter

A successful audit is **not proof of installation or runtime success**. It does
not check native shared libraries, OS packages, GPU drivers, vulnerabilities,
malware, wheel provenance, or whether package metadata is truthful. Use
[auditwheel](https://github.com/pypa/auditwheel) for relevant native-library
inspection and test your application on the destination.

Do not manufacture a remote target by changing only `python_version` or a
platform tag in a captured file. Capture a complete environment or explicitly
supply every supported marker value and an accurate tag list. Missing marker
keys are rejected instead of silently using the audit machine's values.

Wheel archives are untrusted input. Metadata read limits reduce some malformed
archive risks, but this tool is not a sandbox. ZIP64 archives and inputs above
the documented [inspection limits](docs/architecture.md#inspection-limits) are
rejected. See [SECURITY.md](SECURITY.md).

## Troubleshooting

| Finding or symptom | What to check |
| --- | --- |
| Missing dependency | Was the bundle assembled for the intended target and all requested extras? |
| No compatible wheel | Does a wheel match the destination interpreter, ABI, and platform tags? |
| Python version mismatch | Check the wheel's `Requires-Python` and destination interpreter. |
| Multiple reachable versions | Rebuild a curated bundle with one version per distribution. |
| Invalid target JSON | Capture again on the destination; keep the full marker environment and tag list. |
| Unsupported direct URL or source input | Resolve or build it with your package manager, then audit wheels using named requirements. |
| Audit succeeds, application fails | Investigate native dependencies and runtime behavior; these are outside metadata closure. |

For a bug report, include the command, redacted target, JSON finding, and a small
reproduction. Do not upload private wheels, credentials, or proprietary metadata.

## Development and maintenance

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, checks, and contribution policy;
[architecture](docs/architecture.md) for scope and trust boundaries; and
[release process](docs/releasing.md) for versioning and distribution.

The project is maintained in [cocabot/wheelhouse-preflight](https://github.com/cocabot/wheelhouse-preflight).
The initial implementation is AI-assisted. Code, tests, limitations, and actual
public maintenance records are the evidence for its behavior. No external
adoption or independent review is claimed merely because this repository exists.

Licensed under [MIT](LICENSE).
