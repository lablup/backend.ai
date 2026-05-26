from __future__ import annotations

from importlib.metadata import distributions
from pathlib import Path
from typing import Any

import click

_BACKEND_DIST_PREFIX = "backend.ai-"


def _collect_dist_versions() -> dict[str, str]:
    """Collect versions of installed backend.ai-* distributions."""
    versions: dict[str, str] = {}
    for dist in distributions():
        name = dist.metadata["Name"]
        if name and name.lower().startswith(_BACKEND_DIST_PREFIX):
            versions[name] = dist.version
    return versions


def _collect_namespace_versions() -> dict[str, str]:
    """
    Collect versions from VERSION files under the `ai.backend` namespace package.

    This handles dev-mode layouts where subpackages are loaded directly from
    the source tree and are not registered as separate distributions.
    Walks one level into nested namespace packages (e.g., `ai.backend.appproxy.*`)
    so multi-distribution namespaces are covered.
    """
    versions: dict[str, str] = {}
    try:
        import ai.backend as ns
    except ImportError:
        return versions
    seen: set[Path] = set()
    for root_str in ns.__path__:
        root = Path(root_str)
        if not root.is_dir():
            continue
        for child in sorted(root.iterdir()):
            if not child.is_dir() or child in seen:
                continue
            seen.add(child)
            version_file = child / "VERSION"
            if version_file.is_file():
                key = f"{_BACKEND_DIST_PREFIX}{child.name.replace('_', '-')}"
                versions.setdefault(key, version_file.read_text().strip())
                continue
            # Recurse one level for namespace subpackages (e.g., appproxy/*).
            for grand in sorted(child.iterdir()):
                if not grand.is_dir():
                    continue
                version_file = grand / "VERSION"
                if not version_file.is_file():
                    continue
                parent = child.name.replace("_", "-")
                leaf = grand.name.replace("_", "-")
                key = f"{_BACKEND_DIST_PREFIX}{parent}-{leaf}"
                versions.setdefault(key, version_file.read_text().strip())
    return versions


def collect_versions() -> list[tuple[str, str]]:
    """Return sorted (name, version) pairs of backend.ai-* packages."""
    merged = _collect_namespace_versions()
    for name, version in _collect_dist_versions().items():
        merged[name] = version
    return sorted(merged.items())


def print_version(ctx: click.Context, _param: click.Parameter, value: Any) -> None:
    if not value or ctx.resilient_parsing:
        return
    versions = collect_versions()
    if not versions:
        click.echo("No backend.ai-* packages found.")
    else:
        width = max(len(name) for name, _ in versions)
        for name, version in versions:
            click.echo(f"{name:<{width}}  {version}")
    ctx.exit()
