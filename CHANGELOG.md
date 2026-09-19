# Changelog

User-facing changes are recorded here. Version numbers follow Semantic Versioning;
before 1.0, a minor version may change CLI or JSON behavior. Patch releases are
reserved for compatible fixes. Published versions and artifacts are recorded in
[GitHub Releases](https://github.com/cocabot/wheelhouse-preflight/releases).

## 0.1.0 — 2026-09-19

Initial release. Publication and attached artifacts are confirmed only by the
corresponding GitHub Release, not by this changelog entry.

- Capture the local interpreter's complete marker environment and ordered wheel tags.
- Audit local wheel metadata against explicit roots, extras, and a target manifest.
- Identify dependency closure failures, incompatible wheel tags, and Python constraints.
- Return text or versioned JSON diagnostics without installing or executing wheel contents.
- Reject invalid or unsupported inputs, including ambiguous reachable versions.
- Provide automated checks, source and wheel builds, and a gated GitHub release workflow.

Limitations: no package resolution, downloads, source builds, direct-URL resolution,
native-library inspection, vulnerability scanning, or runtime guarantee.
