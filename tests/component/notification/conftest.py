from __future__ import annotations

from collections.abc import AsyncIterator
from unittest.mock import MagicMock

import pytest

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.data.notification.types import (
    NotificationChannelType,
    NotificationRuleType,
    WebhookSpec,
)
from ai.backend.common.dto.manager.notification import (
    CreateNotificationChannelRequest,
    CreateNotificationRuleRequest,
    NotificationChannelDTO,
    NotificationRuleDTO,
)
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


@pytest.fixture()
async def webhook_channel(
    admin_registry: BackendAIClientRegistry,
) -> AsyncIterator[NotificationChannelDTO]:
    """Pre-seeded webhook channel for use in processing tests."""
    result = await admin_registry.notification.create_channel(
        CreateNotificationChannelRequest(
            name="fixture-webhook-channel",
            description="Fixture webhook channel for component tests",
            channel_type=NotificationChannelType.WEBHOOK,
            spec=WebhookSpec(url="https://example.com/webhook"),
            enabled=True,
        )
    )
    yield result.channel
    await admin_registry.notification.delete_channel(result.channel.id)


@pytest.fixture()
async def notification_rule(
    admin_registry: BackendAIClientRegistry,
    webhook_channel: NotificationChannelDTO,
) -> AsyncIterator[NotificationRuleDTO]:
    """Pre-seeded SESSION_STARTED notification rule linked to webhook_channel."""
    result = await admin_registry.notification.create_rule(
        CreateNotificationRuleRequest(
            name="fixture-notification-rule",
            description="Fixture rule for component tests",
            rule_type=NotificationRuleType.SESSION_STARTED,
            channel_id=webhook_channel.id,
            message_template="Session {{ session_name }} started ({{ session_type }})",
            enabled=True,
        )
    )
    yield result.rule
    await admin_registry.notification.delete_rule(result.rule.id)
