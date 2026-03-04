from __future__ import annotations

import pytest

from ai.backend.manager.api.rest.auth.registry import register_auth_routes
from ai.backend.manager.api.rest.notification.registry import register_notification_routes
from ai.backend.manager.api.rest.types import ModuleRegistrar


@pytest.fixture()
def server_module_registrars() -> list[ModuleRegistrar]:
    """Load only the modules required for notification-domain tests."""
    return [register_auth_routes, register_notification_routes]
