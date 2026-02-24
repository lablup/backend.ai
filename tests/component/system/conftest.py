from __future__ import annotations

import pytest

from ai.backend.manager.api.types import CleanupContext


@pytest.fixture()
def server_subapp_pkgs() -> list[str]:
    """No subapps needed — the hello() handler is on the root app."""
    return []


@pytest.fixture()
def server_cleanup_contexts() -> list[CleanupContext]:
    """No cleanup contexts needed — hello() has no DB/Redis/etc dependencies."""
    return []
