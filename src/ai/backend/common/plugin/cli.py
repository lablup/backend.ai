from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class PluginCLIContext(Protocol):
    """What a plugin command under the `ag`/`mgr` group may read from the group's context."""

    @property
    def config_path(self) -> Path | None:
        """The group's `--config` value, or None to discover the daemon's config file."""
        ...
