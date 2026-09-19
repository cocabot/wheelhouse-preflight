# Problem evidence and scope

Last source check: **2026-09-17 (UTC)**.

This document explains why a small, offline wheelhouse auditor is worth testing
with users. It distinguishes upstream facts from product hypotheses. Upstream
requests demonstrate a problem; they do **not** demonstrate adoption of
wheelhouse-preflight, endorsement by those projects, or demand for this particular
implementation.

## Intended user and job

A Python release or platform engineer has collected wheels on a connected build
machine and will transfer them to another environment. The destination may have
a different operating system, architecture, or Python version, and may have no
package-index access. Before transfer, the engineer wants to identify missing or
incompatible Python distributions in the bundle without installing them or
executing their contents.

The proposed audit uses explicitly supplied target-environment information. It
does not assume that the build machine is the deployment target.

## Observed demand

| Source | Observed fact | Relevance and limit |
| --- | --- | --- |
| [pip issue 13442: Download for target environment](https://github.com/pypa/pip/issues/13442) | The reporter describes collection on one OS and Python version for an air-gapped destination with another, and missing target-specific dependencies. The issue was open at the source check. | Concrete cross-environment deployment workflow. This is a request to improve pip, not a request for this auditor. |
| [pip issue 11664: Filtering flags and environment markers](https://github.com/pypa/pip/issues/11664) | The upstream issue consolidates reports that wheel-selection flags do not change the environment used to evaluate dependency markers. It also explains that the complete marker environment cannot be inferred from those flags. The issue was open at the source check. | Supports using a captured target description rather than guessing marker values from a platform name. |
| [uv issue 3163, offline-bundle report](https://github.com/astral-sh/uv/issues/3163#issuecomment-2103079257) | A user needs dependency bundles for firewall-restricted destinations and requests cross-platform downloads. | Independent report of the deployment context; no evidence that this user wants or uses this project. |
| [uv issue 3163, security-scanning report](https://github.com/astral-sh/uv/issues/3163#issuecomment-2229179802) | A user collects wheel or source artifacts because their scanning system consumes an artifact directory. | Shows artifact directories are an integration boundary. This project is not a vulnerability scanner. |
| [uv issue 3163, offline-install workflow](https://github.com/astral-sh/uv/issues/3163#issuecomment-3532854220) | A user gives a concrete export, download, build, transfer, and offline-install workflow. | An auditor could fit between bundle assembly and transfer. That usefulness is a product hypothesis. |
| [uv issue 3163, AWS Glue example](https://github.com/astral-sh/uv/issues/3163#issuecomment-4270656327) | A 2026 report supplies another target-specific wheel collection use case. | Confirms that the general workflow continued to arise in 2026; it does not establish a specific missing audit feature. |

The upstream problem reports are evidence of a recurring workflow and failure
mode. They are not surveys, market-size estimates, testimonials, user counts, or
measurements of prevented failures.

## Existing tools and the narrower opportunity

| Tool | Verified capability | Implication for this project |
| --- | --- | --- |
| [pip download](https://pip.pypa.io/en/stable/cli/pip_download/) | Collects distributions and dependencies, accepts target wheel-selection flags, and the checked v26.2.1 documentation includes experimental `pylock.toml` input through `-r`. | A new generic downloader or a claim that pip cannot consume pylock would be poorly justified. Continue using pip where it solves the collection job. |
| [pip check](https://pip.pypa.io/en/stable/cli/pip_check/) | Verifies dependency compatibility in an installed environment. | The proposed input is an uninstalled wheel directory plus an explicit target description. |
| [PEX](https://docs.pex-tool.org/buildingpex.html#complete-platform) | Supports complete target descriptions containing `marker_environment` and ordered `compatible_tags`. Its documentation also shows building from a local wheelhouse with `--no-index`. | PEX already offers a capable alternative for offline resolution and packaging. Reuse its target-description shape rather than inventing an incompatible one. Do not claim cross-platform checking is otherwise impossible. |
| [PEX distribution download implementation](https://github.com/pex-tool/pex/blob/main/pex/cli/commands/pip/download.py) | Has a command dedicated to downloading distributions rather than building a PEX. | Artifact collection itself is not a differentiator. |
| [uv-pack](https://github.com/davnn/uv-pack/blob/main/README.md) | Bundles a locked uv environment, wheels, and an optional Python interpreter for offline installation. Its checked README states that packing expects the build and usage platforms to match. | A useful adjacent tool. An independent auditor could inspect bundles from multiple producers; this integration remains unvalidated. |
| [check-wheel-contents](https://github.com/jwodder/check-wheel-contents) | Checks wheel contents for packaging mistakes such as unwanted files and incorrect top-level contents. | Retain that tool for package-author checks. The proposed audit follows dependencies across wheels for a target. |
| [auditwheel](https://github.com/pypa/auditwheel) | Inspects native-library dependencies and platform compatibility of Linux and Android wheels, and can repair certain wheels. | Native-library compatibility is outside the proposed audit. A passing metadata audit cannot replace auditwheel or a deployment test. |

The opportunity is a small, read-only CI check that reports the problems found
in an existing wheel bundle, including the requirement and dependency path that
caused each finding. Its proposed advantages are a narrow interface, structured
output, and no installation or artifact execution. These are design choices, not
yet evidence of user preference, superiority, speed, or adoption.

The comparison is a bounded review of relevant primary sources, not a proof that
no equivalent tool exists. Existing PEX and pip workflows should remain visible
alternatives in user documentation.

## Initial audit contract

This is the scope selected from the research. The README and CLI reference define
the implemented interface; this document alone does not certify implementation.

| Input | Required meaning |
| --- | --- |
| Wheel directory | Locally available `.whl` artifacts to inspect. |
| Root requirements | The application or libraries, version constraints, and extras to audit. |
| Target description | The complete supported PEP 508 marker environment and ordered compatible wheel tags, captured on the destination or deliberately supplied by the operator. PEX complete-platform JSON is the intended interoperability format. |

The audit should inspect wheel metadata and traverse the dependencies applicable
to that target and the requested extras. It should explain missing distributions,
unsatisfied version constraints, incompatible wheel tags, incompatible
`Requires-Python`, ambiguous selections, invalid metadata, and inputs it cannot
safely evaluate. Structured results should be deterministic enough for CI tools
to consume, without scraping terminal prose.

For the initial scope, a bundle with multiple viable versions of one distribution
is ambiguous. The auditor should report the ambiguity rather than impersonate a
dependency resolver or silently choose a version. A pinned, single-version bundle
is the most useful initial input.

Initial exclusions:

- Dependency resolution with backtracking, package downloading, and installation.
- Source-distribution builds, editable projects, and VCS or direct-URL resolution.
- Native shared-library availability, GPU drivers, operating-system packages,
  runtime behavior, and successful application startup.
- Vulnerability scanning, malware detection, provenance attestation, or a claim
  that a wheel is safe to execute.
- `uv.lock` or `pylock.toml` ingestion unless separately implemented and documented.

A successful result can establish only that the supported metadata checks found
no problem for the supplied roots, artifacts, and target. It is not a guarantee
of installation success or runtime correctness. Incorrect target descriptions
and incomplete package metadata remain outside what static inspection can prove.

## Standards and implementation risks

Use the current PyPA specifications as the behavioral reference:

- [Dependency specifiers](https://packaging.python.org/en/latest/specifications/dependency-specifiers/): requirements, extras, and environment-marker semantics.
- [Core metadata](https://packaging.python.org/en/latest/specifications/core-metadata/): package identity, `Requires-Dist`, `Requires-Python`, and declared extras.
- [Platform compatibility tags](https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/): wheel compatibility tags.

High-value validation cases follow from the observed failure mode:

1. A dependency guarded by a Windows marker is required when auditing a Windows
   target from a Linux host, and is omitted for the corresponding Linux target.
2. Extras reached through different dependency paths are combined; dependency
   cycles terminate; later constraints cannot leave an earlier selection falsely
   accepted.
3. Missing target-marker values, malformed metadata, unsupported references, and
   ambiguous versions produce explicit findings rather than host-derived guesses
   or a false successful result.
4. Artifact inspection does not execute a wheel, import its modules, extract it to
   the filesystem, or contact a package index. Archive size and metadata-read
   limits protect against malformed or excessive inputs.
5. A passing synthetic fixture is labeled as a test fixture. It is not recorded
   as an external integration or real-world adoption.

## What remains to be established

| Question | Current evidence |
| --- | --- |
| Does the general deployment problem exist? | Supported by upstream reports and documented tool behavior. |
| Is this narrow audit a useful addition to existing workflows? | Plausible inference; requires independent users trying it. |
| Is it easier to adopt than an existing PEX or pip workflow? | Unmeasured. |
| Does it prevent real transfer or deployment failures? | Unmeasured. Reproducing upstream-style failures in tests proves behavior, not field impact. |
| Are there external users, integrations, or dependents? | None established by this research. |

The next product evidence should come from reproducible examples and actual
independent use. Internal tests, author-controlled examples, downloads made for
validation, and upstream issue reactions must not be reported as external
adoption.
