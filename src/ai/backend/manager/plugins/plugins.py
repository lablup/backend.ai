from __future__ import annotations

from dataclasses import dataclass

from ai.backend.manager.plugins.auth import AuthPlugin


@dataclass
class ManagerPlugins:
    """The plugins the manager loaded at startup, registered once and injected from here."""

    auth_plugin: AuthPlugin | None
