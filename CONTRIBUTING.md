# Contributing

Contributions should improve real wheelhouse audit workflows. A small failing
fixture, a clearer diagnostic, or a documented compatibility case is valuable.
Please explain the user problem before proposing a larger feature.

## Development setup

Use Python 3.11 or newer and a virtual environment:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e . -r requirements-dev.txt
python -m unittest discover -s tests -v
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m build
```

On Windows, activate with `.venv\Scripts\activate`. The test suite uses the
standard-library `unittest` runner; it must not need network access or execute
code inside fixture wheels. When a change affects closure behavior, add a
regression test that shows the relevant dependency or target difference.

## Bugs and feature proposals

Use the issue templates. Include the command, version, a minimal reproduction,
expected behavior, and actual findings. Redact private paths and metadata. Do not
attach credentials or private distributions. Report vulnerabilities using
[SECURITY.md](SECURITY.md) instead of posting exploit details in an issue.

Issues need an actual problem or improvement. We do not ask people to open issues,
PRs, or stars for activity metrics. Author-created synthetic fixtures and validation
downloads must not be presented as external users or adoption.

## Pull requests

Keep changes focused. Describe why the change is needed, the resulting behavior,
how it was tested, and compatibility implications. Update documentation and the
changelog when public behavior changes. Do not change generated fixtures merely
to hide a regression.

AI-assisted contributions are welcome. State material AI assistance and review
the resulting code, tests, licenses, and factual claims. Authors remain responsible
for submitted content. An automated review is not an independent human review.

Contributions are licensed under the repository's MIT license. Do not include
code or documentation that you lack permission to contribute; retain any required
third-party attribution. No contributor agreement is currently required.

## Review and triage

The repository owner, `@cocabot`, is the initial release and maintenance contact.
This describes responsibility, not a claim that any particular review or support
action has already happened. Public issues, PRs, and releases record actual work.

Maintainers classify reproducible defects as `bug`, user-driven improvements as
`enhancement`, and documentation issues as `documentation`. Add `help wanted` or
`good first issue` only when the work has a clear scope and sufficient context.
Security reports are handled privately where possible. Labels do not imply a
response-time guarantee.

Be respectful and specific. Critique code and arguments rather than people. Do
not harass contributors or post private information. Maintainers may moderate
abusive or irrelevant content. There is no promised review or support deadline.
