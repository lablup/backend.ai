from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.api.rest.notification.handler import NotificationHandler
from ai.backend.manager.api.rest.notification.registry import register_notification_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.notification.notification_center import NotificationCenter
from ai.backend.manager.repositories.notification.repository import NotificationRepository
from ai.backend.manager.services.notification.processors import NotificationProcessors
from ai.backend.manager.services.notification.service import NotificationService


@pytest.fixture()
def notification_processors(
    database_engine: ExtendedAsyncSAEngine,
    notification_center: NotificationCenter,
) -> NotificationProcessors:
    repo = NotificationRepository(database_engine)
    service = NotificationService(repo, notification_center)
    return NotificationProcessors(
        service=service, action_monitors=[], validators=MagicMock(spec=ActionValidators)
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    notification_processors: NotificationProcessors,
) -> list[RouteRegistry]:
    """Load only the modules required for notification-domain tests."""
    return [
        register_notification_routes(
            NotificationHandler(notification=notification_processors), route_deps
        ),
    ]
