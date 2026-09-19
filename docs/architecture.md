# Architecture and audit contract

## Inputs and outputs

The CLI accepts a local wheel directory, repeated PEP 508 root requirements, and
an explicit target manifest. It emits a text summary or a JSON report and a
process exit status. There is no network client or package installation step in
the audit path.

The target shape follows PEX complete-platform descriptions:

```json
{
  "marker_environment": {
    "implementation_name": "cpython",
    "implementation_version": "3.11.9",
    "os_name": "posix",
    "platform_machine": "x86_64",
    "platform_release": "example",
    "platform_system": "Linux",
    "platform_version": "example",
    "python_full_version": "3.11.9",
    "platform_python_implementation": "CPython",
    "python_version": "3.11",
    "sys_platform": "linux"
  },
  "compatible_tags": ["py3-none-any"]
}
```

This is a deliberately minimal illustrative target that permits only universal
pure-Python wheels. It is not a complete tag list for a real Linux interpreter.
Use the `target` command on the deployment interpreter for real audits. All marker
keys are required, tags are ordered and expanded, and values are not filled from
the audit host. A fabricated target yields only a result about that fabrication.

## Responsibilities

| Module | Responsibility |
| --- | --- |
| `target.py` | Capture and validate explicit marker environments and compatible tags. |
| `wheel.py` | Inspect wheel filenames and metadata without extraction or execution. |
| `audit.py` | Follow applicable requirements, collect constraints/extras, and report closure defects. |
| `cli.py` | Parse arguments, load inputs, render findings, and choose exit status. |

`packaging` supplies standard requirement, version, marker, and wheel-tag parsing.
The project does not maintain a competing implementation of these standards.

## Deliberate product boundary

The auditor expects a curated bundle with a single version for each reachable
distribution. It may select among compatible platform wheels of that same
version using target tag preference. It does not search a graph of alternative
versions or attempt to match every package-manager resolver decision.

Requirements are followed only when their marker applies to the supplied
target and active extras. Extras discovered through different paths must be
combined; cycles must terminate; later requirements must not silently bypass
earlier constraints. Unsupported references and ambiguous versions prevent a
successful audit rather than triggering downloads or guessed selections.

The CLI is the supported interface for 0.1. Internal Python modules are not yet
a stable public API. JSON includes a schema version; automation should tolerate
additional fields but must check the exit status. A future incompatible JSON
change requires a new schema version and a migration note.

## Trust boundaries

Wheel archives, metadata fields, target files, and filesystem names are untrusted.
Reading metadata must not import wheel code or extract archive members. Metadata
and target limits exist to bound reads; they are not a guarantee against every
resource-exhaustion attack. Text diagnostics escape control characters; JSON
provides structured, escaped output.

Wheel files must be regular files. Symlinks are rejected; where available,
`O_NOFOLLOW` is used when opening files. The reader checks the opened file's
identity against the filesystem entry and detects changes while reading. These
checks do not make a concurrently modified directory a trusted snapshot.

The target manifest is trusted as a description supplied by the operator. The
auditor cannot prove it matches a destination. Package metadata is also a claim
made by a package author, not proof of actual runtime dependencies.

## Inspection limits

These are explicit compatibility boundaries, not configurable resource promises.
An archive that exceeds them is rejected even if another packaging tool can read it.

| Input | Limit or supported form |
| --- | --- |
| Wheelhouse | At most 10,000 wheels. |
| Individual wheel | At most 1 GiB. |
| ZIP central directory | At most 8 MiB and 50,000 members, checked before ZIP object allocation. |
| ZIP format | No ZIP64 or multi-disk archives. |
| Package `METADATA` | At most 2 MiB. |
| `WHEEL` metadata | At most 64 KiB. |
| Metadata compression | Stored or Deflate; encrypted metadata is rejected. |
| Compressed wheel tags | At most 256 combinations per tag and 1,024 tags in total. |
| Target JSON | At most 2 MiB and 20,000 expanded, unique compatible tags. |

Archive metadata checks are deliberately conservative. The tool hashes selected
artifacts for reporting but does not check every file's `RECORD` hash or establish
the publisher's identity. Unselected malformed wheels can still make the audit
fail because the supplied directory is inspected as a bundle.

## Non-goals

- Replacing pip, uv, PEX, or lockfile generation.
- Building source distributions or resolving editable/VCS/direct-URL requirements.
- Checking native shared libraries, system packages, or application startup.
- Detecting malware, CVEs, or verifying artifact signatures and provenance.

Keep these boundaries explicit in diagnostics, documentation, and future
feature decisions. Add a feature when a demonstrated user workflow benefits;
avoid expanding the tool solely to create repository activity.
