from __future__ import annotations

import pytest

from ai.backend.manager.api.types import CleanupContext
from ai.backend.manager.server import monitoring_ctx


@pytest.fixture()
def server_subapp_pkgs() -> list[str]:
    """No subapps needed — the hello() handler is on the root app."""
    return []


@pytest.fixture()
def server_cleanup_contexts() -> list[CleanupContext]:
    """Provide monitoring_ctx so that exception_middleware can access
    root_ctx.error_monitor and root_ctx.stats_monitor.

    monitoring_ctx only depends on root_ctx.etcd (from mock_etcd_ctx)
    and root_ctx.config_provider (from server fixture), both already
    initialized before cleanup contexts run.
    """
    return [monitoring_ctx]
