# Qualification evidence record

**Snapshot: 2026-09-18, first implementation publication preparation. Overall
application readiness: WEAK — not ready to apply.** This is the project's evidence
assessment, not an OpenAI decision. Public CI and release URLs must be added after
those events occur.

## Project and current evidence

`wheelhouse-preflight` helps Python release and deployment maintainers check a
wheel collection before taking it to a machine without internet access. It
statically checks explicit root requirements, transitive dependencies, extras,
versions, Python requirements, and wheel tags against a target machine's
collected PEP 508 environment and compatibility tags. It neither installs nor
executes dependency code and does not contact a package index. It is not a
backtracking resolver, shared-library validator, CVE scanner, or guarantee that
installed software will run.

| ID | Evidence | What it establishes and limits |
| --- | --- | --- |
| E1 | [Public repository](https://github.com/cocabot/wheelhouse-preflight) and [MIT license commit](https://github.com/cocabot/wheelhouse-preflight/commit/36b299fd740162ee20c4c1bc5b0fcd0367701a87) | Public repository and MIT license: **CONFIRMED**. This snapshot precedes publication of the implementation. |
| E2 | Local working-tree validation: 55 tests pass; lint, strict mypy, wheel build, and clean installation pass | Technical implementation evidence. Public code, commit-specific CI logs, and release validation URLs are pending. |
| E3 | Local static check of actual Click 8.1.8 / Colorama 0.4.6 wheels for a native Linux target passes | A real-package compatibility example, not external use, full platform coverage, or proof of runtime success. |
| E4 | Owner created the repository and delegated the development scope; agents performed architecture, implementation, and verification work | An AI-assisted maintainer workflow. It does not establish independent human review or an ongoing public maintenance record. |
| E5 | [Repository metadata](https://api.github.com/repos/cocabot/wheelhouse-preflight), observed 2026-09-17T22:49:48Z: 0 stars, 0 forks | A dated discovery snapshot only. Neither measure establishes use. |

Distribution is being prepared as an installable Python CLI. No published package
or release is claimed in this snapshot. Package downloads, external dependents,
installations, users, integrations, external contributors, and genuine community
reports are **UNKNOWN**. Local installations and agent runs are development
validation, not adoption. Missing observations must not be entered as zero.

## Official program information

Official pages were checked on **2026-09-17**. Recheck them before applying and
when an official change becomes known.

| Official source | Relevant published information |
| --- | --- |
| [Application form](https://openai.com/form/codex-for-oss/) | Active OSS maintainers may apply. OpenAI considers meaningful usage, broad adoption, or clear ecosystem importance and active maintenance. The form requests a public profile and repository, primary/core maintainer role, and a qualification explanation of at most 500 characters. |
| [Program overview](https://developers.openai.com/community/codex-for-oss) | Selected maintainers can receive six months of ChatGPT Pro with Codex, possible API credits, and conditional Codex Security access. Security access is reviewed individually; important ecosystem roles can be explained even when a project does not fit the usual criteria. |
| [Program terms](https://learn.chatgpt.com/docs/codex-for-oss-terms) | A valid ChatGPT account and accurate identity, repository, and role information are required. OpenAI can verify affiliation or control; selection and benefits remain discretionary and may change. Submitting an application accepts the terms. |

These pages publish no numerical minimum for stars, downloads, project age,
commits, issues, PRs, or releases. They do not disclose a formula or guarantee
acceptance. This document does not submit an application or accept the terms.

The **project's own threshold** additionally requires a usable public OSS
release, genuine externally verifiable use, demonstrated primary/core
maintenance responsibility, concrete ecosystem value, and several public URLs
supporting an honest application. Appropriate triage, review, releases, security,
and support must serve actual project needs. This is a project decision, not an
additional OpenAI rule. Readiness does not depend on elapsed time or quotas.

## Qualification readiness

`CONFIRMED` means direct evidence verifies the scoped claim; `STRONG` means
substantial corroborated evidence; `PARTIAL` means material gaps remain; `WEAK`
means insufficient evidence; `UNKNOWN` means no reliable observation. These
ratings do not estimate OpenAI's acceptance probability.

| # | Dimension | Rating | Evidence and remaining gap |
| --- | --- | --- | --- |
| 1 | Active OSS project | PARTIAL | E1 confirms the public repository and license. E2 is locally verified code awaiting publication and public CI. |
| 2 | Real project utility | PARTIAL | E2–E3 demonstrate scoped checks and a real-package example. Independent user validation is absent. |
| 3 | External usage | UNKNOWN | No verified external user, dependent, installation, or integration evidence. |
| 4 | Ecosystem value | PARTIAL | The explicit-target offline wheelhouse workflow and E3 establish a concrete technical use case. External adoption and ecosystem impact are unproven. |
| 5 | Active maintenance | PARTIAL | E2 records implementation and verification work. Ongoing public fixes and responsibility are not yet demonstrated. |
| 6 | Issue triage | UNKNOWN | No real issue investigation or response is recorded. |
| 7 | Pull Request review | UNKNOWN | No public substantive PR review is recorded; local agent verification is not independent human review. |
| 8 | Release management | PARTIAL | E2 verifies a build and clean installation locally. A versioned public release, changelog, and artifact evidence are pending. |
| 9 | Core maintainer responsibility | PARTIAL | E1 and E4 establish repository creation and delegated AI-assisted work. Sustained public decisions, review, triage, releases, and support remain unproven. |
| 10 | Project legitimacy | PARTIAL | E1 confirms public identity and MIT licensing; E2 supports working code. Public implementation, honest limitations, and provenance still need publication. |
| 11 | Public evidence quality | PARTIAL | E1 supplies stable public identity/license evidence. Verification, release, maintenance, and external-use URLs are missing. |
| 12 | Overall application readiness | WEAK | Genuine external use and ongoing maintenance are not established; public implementation, CI, and distribution are still being prepared. |

## Bottleneck and next action

The immediate bottleneck is converting the verified local implementation into
publicly inspectable code, passing CI, and an installable release. The next step
is the implementation PR, its checks, and release validation. After publication,
genuine external use and maintenance responsibility become the key gaps; more
internal features or activity alone cannot fill them. Handle a real user's
reported problem ahead of cosmetic work or activity generation.

## Evidence updates

Update after publication, a completed check, release, real issue, substantive PR
review, external integration/use report, compatibility/security fix, or official
policy change. Record the result, reassess the affected dimensions, and name the
new bottleneck. Do not manufacture events to improve a rating.

```text
Evidence ID and category: identity | adoption | community | maintenance | maintainer-role
Observed at (UTC):
Public URL(s), commit SHA/version, and observation method:
Fact or measured value, scope, unit, and measurement window:
Actor: owner | external person | bot | AI-assisted maintainer workflow
What this proves; limitations and unknowns:
Affected dimensions and rating change, with reasoning:
```

Use stable public URLs for architectural decisions, triage, reviews, fixes,
releases, and safe-to-disclose security work. Keep owner and external activity
distinct. Downloads are not unique users; record their source and window. Never
include credentials, private reports, or personal account information. Do not
attribute agent-authored work to the owner's manual effort, count agents as
external people, or invent human reviews, usage figures, or testimonials.

When the project threshold is evidenced, prepare the qualification summary,
repository and project description, ecosystem value, usage and maintainer
records, maintenance records, categorized public URLs, weak points, and factual
application draft. Recheck current form limits and terms. Applying remains a
separate action requiring the applicant's review of the actual submission and
any personal declarations.
