# Security policy

## Scope

wheelhouse-preflight reads untrusted wheel ZIP archives, target JSON, and Python
package metadata. It does not install the packages, extract their contents,
import their code, or contact a package index during an audit. Resource limits
reduce some malformed-input risks; they do not make this process a sandbox.

The reader rejects symbolic links and non-regular files, uses `O_NOFOLLOW` where
available, verifies the opened file's identity, and detects changes during a read.
It bounds the ZIP central directory before parsing and limits metadata reads and
tag expansion. ZIP64 is unsupported. See the exact
[inspection limits](docs/architecture.md#inspection-limits).

Run it without elevated privileges. Apply normal resource isolation when
processing untrusted uploads. A passing audit makes no claim about malware,
vulnerabilities, artifact authenticity, or runtime safety. Verify downloaded
artifacts through your normal supply-chain controls.

Target manifests and reports can expose OS details, private package names,
versions, and paths. Review them before sharing. Never attach credentials or
private wheels to a public issue.

## Reporting a vulnerability

Use GitHub's **Report a vulnerability** option on the repository Security tab if
private vulnerability reporting is enabled:

https://github.com/cocabot/wheelhouse-preflight/security

If that option is unavailable, open an issue asking the maintainer to establish
a private reporting channel. **Do not include vulnerability details, proof-of-
concept payloads, or affected private data in that public issue.** No private
email address is claimed by this policy.

Once a private channel exists, provide the affected version, reproduction,
expected impact, and any proposed fix. The maintainer will assess the report and
coordinate a fix and disclosure where appropriate. Response times are not
guaranteed.

## Supported versions

This is an initial 0.x project. Security fixes target the latest released 0.x
version; there is no separate long-term-support branch. Check GitHub Releases for
the actual published versions. Do not infer that a version is published from a
development changelog entry.
