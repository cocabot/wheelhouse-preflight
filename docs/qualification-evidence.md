# Qualification evidence record

**Snapshot: 2026-09-19. Overall application readiness: WEAK — not ready to apply.**
This is the project's evidence assessment, not an OpenAI decision.

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
| E1 | [Public repository](https://github.com/cocabot/wheelhouse-preflight), [MIT license](https://github.com/cocabot/wheelhouse-preflight/blob/2fc6411fd52867f93da59710c20da2b5b6c92e97/LICENSE), [merged implementation PR #1](https://github.com/cocabot/wheelhouse-preflight/pull/1) | Public working implementation, documentation, license and owner-controlled integration. |
| E2 | [PR CI](https://github.com/cocabot/wheelhouse-preflight/actions/runs/35427287472) | 55 tests across the configured Python 3.11–3.14 / Linux, Windows and macOS matrix; minimum packaging version, lint, formatting, strict types, build and clean-wheel installation passed. This is a matrix, not every OS/Python combination. |
| E3 | Real Click 8.1.8 / Colorama 0.4.6 validation in E2 | Complete bundles passed; deliberately omitting Colorama failed on Windows and passed on Linux/macOS as expected. Maintainer testing, not external adoption or runtime guarantees. |
| E4 | [AI-assisted investigation](https://github.com/cocabot/wheelhouse-preflight/pull/1#issuecomment-5739990061), [test compatibility fix](https://github.com/cocabot/wheelhouse-preflight/commit/04db3ffcb0f1004866423cdf2f5292ced4639687) | A real Python 3.14 CI failure was investigated and fixed. The owner delegated development and release work to agents. This is not independent human review or proof of sustained human activity. |
| E5 | [Repository metadata](https://api.github.com/repos/cocabot/wheelhouse-preflight), observed 2026-09-17T22:49:48Z: 0 stars, 0 forks | Historical discovery snapshot only, not evidence of use. |
| E6 | [Release v0.1.0](https://github.com/cocabot/wheelhouse-preflight/releases/tag/v0.1.0), [release validation](https://github.com/cocabot/wheelhouse-preflight/actions/runs/35427951692) | Versioned wheel, source archive and SHA256SUMS published after validation of merged commit 2fc6411fd52867f93da59710c20da2b5b6c92e97. Checksums establish file integrity comparisons, not publisher authenticity. |

Distribution is through GitHub Releases. No PyPI publication is claimed.
Package downloads, external dependents, installations, users, integrations,
external contributors, and genuine community reports are **UNKNOWN**. Local
installations, CI runs and maintainer downloads are validation, not adoption.
Missing observations must not be entered as zero.

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
| 1 | Active OSS project | CONFIRMED | E1–E2 and E6 establish public working code, license, passing CI and an initial release. This does not establish a long maintenance history. |
| 2 | Real project utility | PARTIAL | E2–E3 demonstrate scoped checks and a real-package failure case. Independent user validation is absent. |
| 3 | External usage | UNKNOWN | No verified external user, dependent, installation or integration evidence. |
| 4 | Ecosystem value | PARTIAL | E3 and the [demand research](research.md) establish a concrete target-marker problem. Independent adoption and impact are unproven. |
| 5 | Active maintenance | PARTIAL | E4 establishes a real compatibility investigation and fix. Continued maintenance is not yet evidenced. |
| 6 | Issue triage | UNKNOWN | No genuine issue investigation or response is recorded. |
| 7 | Pull Request review | PARTIAL | E1 and E4 contain substantive AI-assisted review findings and CI investigation. No independent human review is claimed. |
| 8 | Release management | CONFIRMED | E6 records a versioned, CI-gated release with changelog and distribution artifacts. Future release continuity remains unproven. |
| 9 | Core maintainer responsibility | PARTIAL | E1 and E4 establish owner-controlled, delegated development and release decisions. Sustained triage, review and support remain unproven. |
| 10 | Project legitimacy | CONFIRMED | E1–E3 and E6 establish actual licensed functionality and transparent technical limits. This is not program qualification. |
| 11 | Public evidence quality | PARTIAL | E1–E6 provide inspectable code, PR, fix, CI and release URLs. External-use and sustained-maintenance evidence remain absent. |
| 12 | Overall application readiness | WEAK | Genuine external use and sustained maintenance responsibility are not established. |

## Bottleneck and next action

The primary bottleneck is genuine external use. Versioned GitHub distribution,
a reproducible real-wheel example and explicit limitations now allow others to
evaluate the tool. Next, reduce installation friction through an appropriate
package registry and obtain workflow feedback through relevant, permissioned
channels. Publishing to an owner's registry account requires verified access;
account creation or terms acceptance must be handled by the account holder.
Do not treat promotion, download counters or additional internal features as
proof of adoption. Handle a real user's reported problem ahead of cosmetic work.

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
