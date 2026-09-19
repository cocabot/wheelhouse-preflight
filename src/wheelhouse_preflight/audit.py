"""Conservative dependency-closure audit for curated, single-version wheelhouses."""

from __future__ import annotations

import stat
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from packaging.markers import Marker
from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version

from .target import InputError, Target
from .wheel import MAX_WHEELS, Wheel, read_wheel


@dataclass(frozen=True)
class Issue:
    code: str
    message: str
    path: tuple[str, ...] = ()
    severity: str = "error"
    package: str | None = None


@dataclass
class Report:
    roots: list[str]
    target: Target
    selected: list[dict[str, Any]]
    issues: list[Issue]

    @property
    def exit_code(self) -> int:
        if any(issue.severity == "unsupported" for issue in self.issues):
            return 2
        return 1 if self.issues else 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "status": {0: "ready", 1: "not_ready", 2: "unsupported"}[self.exit_code],
            "scope": (
                "static wheel metadata dependency closure; not a runtime or security guarantee"
            ),
            "roots": list(self.roots),
            "target": self.target.to_dict(),
            "selected": self.selected,
            "issues": [{**asdict(issue), "path": list(issue.path)} for issue in self.issues],
        }


def _marker_applies(marker: Marker | None, target: Target, extra: str = "") -> bool:
    if marker is None:
        return True
    # Supplying every standard marker value prevents packaging's host fallback.
    # extras/dependency_groups require a containing lock-file layer, absent here.
    return marker.evaluate(environment={**target.marker_environment, "extra": extra})


def audit_wheelhouse(directory: Path, roots: list[str], target: Target) -> Report:
    """Audit all reachable dependencies. Never resolve, install, download or execute."""
    if not roots:
        raise InputError("At least one root requirement is required.")
    if not directory.is_dir():
        raise InputError("Wheelhouse must be an existing directory.")
    if len(roots) > MAX_WHEELS:
        raise InputError("Too many root requirements.")
    parsed_roots: list[Requirement] = []
    for root in roots:
        if len(root) > 8192:
            raise InputError("Root requirement exceeds the 8192-character limit.")
        try:
            parsed_roots.append(Requirement(root))
        except InvalidRequirement as exc:
            raise InputError(f"Invalid root requirement: {root}") from exc
    paths = sorted(directory.iterdir(), key=lambda p: p.name)
    paths = [path for path in paths if path.suffix.lower() == ".whl"]
    if len(paths) > MAX_WHEELS:
        raise InputError(f"Wheelhouse exceeds the {MAX_WHEELS}-wheel limit.")
    issues: list[Issue] = []
    by_name: dict[str, list[Wheel]] = {}
    for path in paths:
        try:
            # Avoid blocking on named pipes; archive extraction is never performed.
            if not stat.S_ISREG(path.lstat().st_mode):
                raise InputError("Wheel must be a regular file; symlinks are not followed.")
            wheel = read_wheel(path)
            by_name.setdefault(wheel.name, []).append(wheel)
        except (InputError, OSError) as exc:
            issues.append(Issue("invalid_wheel", f"{path.name}: {exc}", (path.name,)))

    tag_order = {tag: index for index, tag in enumerate(target.compatible_tags)}
    python_version = Version(target.marker_environment["python_full_version"])
    selected: dict[str, Wheel] = {}
    expanded: dict[str, set[str]] = {}
    # Store requirement, causal path, and the parent's currently evaluated extra.
    pending: deque[tuple[Requirement, tuple[str, ...], str]] = deque(
        (req, (str(req),), "") for req in parsed_roots
    )
    seen_edges: set[tuple[str, str, str]] = set()
    active_roots = 0

    def add(
        code: str, message: str, path: tuple[str, ...], name: str, unsupported: bool = False
    ) -> None:
        issue = Issue(code, message, path, "unsupported" if unsupported else "error", name)
        if issue not in issues:
            issues.append(issue)

    while pending:
        req, chain, parent_extra = pending.popleft()
        name = str(canonicalize_name(req.name))
        # Deduplicate dependency edges, not package names: later extras/constraints matter.
        parent = chain[-2] if len(chain) > 1 else "<root>"
        edge_key = (parent, str(req), parent_extra)
        if edge_key in seen_edges:
            continue
        seen_edges.add(edge_key)
        try:
            if not _marker_applies(req.marker, target, parent_extra):
                continue
        except (KeyError, ValueError, TypeError) as exc:
            add("unsupported_marker", f"Cannot evaluate marker on {req}: {exc}", chain, name, True)
            continue
        if len(chain) == 1:
            active_roots += 1
        if req.url:
            add(
                "direct_url",
                f"Direct URL requirement is unsupported: {req.name}.",
                chain,
                name,
                True,
            )
            continue
        if name not in selected:
            candidates = by_name.get(name, [])
            if not candidates:
                add("missing_package", f"No wheel found for {req.name}.", chain, name)
                continue
            versions = {wheel.version for wheel in candidates}
            if len(versions) > 1:
                add(
                    "ambiguous_versions",
                    f"Multiple versions of {name} are present; curate one version before auditing.",
                    chain,
                    name,
                    True,
                )
                continue
            compatible = [wheel for wheel in candidates if wheel.tags & tag_order.keys()]
            if not compatible:
                add(
                    "incompatible_wheel", f"No {name} wheel matches the target's tags.", chain, name
                )
                continue
            compatible = [
                wheel
                for wheel in compatible
                if wheel.requires_python.contains(python_version, prereleases=True)
            ]
            if not compatible:
                add(
                    "requires_python",
                    f"No tag-compatible {name} wheel allows Python {python_version}.",
                    chain,
                    name,
                )
                continue
            ranks = [
                (min(tag_order[tag] for tag in wheel.tags if tag in tag_order), wheel)
                for wheel in compatible
            ]
            best_rank = min(rank for rank, _ in ranks)
            best = [wheel for rank, wheel in ranks if rank == best_rank]
            if len(best) != 1:
                add(
                    "ambiguous_wheels",
                    f"Equally preferred wheels for {name}; retain one build for this target.",
                    chain,
                    name,
                    True,
                )
                continue
            selected[name] = best[0]
        chosen = selected[name]
        if not req.specifier.contains(chosen.version, prereleases=True):
            add(
                "version_mismatch",
                f"{name}=={chosen.version} does not satisfy {req.specifier}.",
                chain,
                name,
            )
        requested_extras = {str(canonicalize_name(extra)) for extra in req.extras}
        for extra in sorted(requested_extras - chosen.provides_extra):
            add("unknown_extra", f"{name} does not declare extra {extra}.", chain, name)
        # Every package is traversed for the base context and each requested extra.
        new_contexts = ({""} | (requested_extras & chosen.provides_extra)) - expanded.setdefault(
            name, set()
        )
        expanded[name].update(new_contexts)
        for extra in sorted(new_contexts):
            for dep in chosen.requires_dist:
                pending.append((dep, (*chain, str(dep)), extra))

    if not active_roots and not issues:
        issues.append(
            Issue("no_active_roots", "All root requirements were excluded by target markers.")
        )
    selection = [
        {
            "name": name,
            "version": str(wheel.version),
            "filename": wheel.path.name,
            "sha256": wheel.sha256,
            "extras": sorted(expanded.get(name, set()) - {""}),
        }
        for name, wheel in sorted(selected.items())
    ]
    return Report(list(roots), target, selection, issues)
