from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ai.backend.plugin.entrypoint import scan_entrypoints


def scan_plugin_entrypoints(
    plugin_group: str,
    allowlist: set[str] | None = None,
    blocklist: set[str] | None = None,
) -> Iterator[tuple[str, Any]]:
    """The name and the loaded object of every entry point in a plugin group.

    What each entry point resolves to is the caller's to check.
    """
    for entrypoint in scan_entrypoints(plugin_group, allowlist=allowlist, blocklist=blocklist):
        yield entrypoint.name, entrypoint.load()
