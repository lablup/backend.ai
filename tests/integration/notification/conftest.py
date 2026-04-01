from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any

import pytest

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.data.notification.types import (
    NotificationChannelType,
    NotificationRuleType,
    WebhookSpec,
)
from ai.backend.common.dto.manager.notification import (
    CreateNotificationChannelRequest,
    CreateNotificationChannelResponse,
    CreateNotificationRuleRequest,
    CreateNotificationRuleResponse,
)

ChannelFactory = Callable[..., Coroutine[Any, Any, CreateNotificationChannelResponse]]
RuleFactory = Callable[..., Coroutine[Any, Any, CreateNotificationRuleResponse]]


@pytest.fixture()
async def channel_factory(
    admin_registry: BackendAIClientRegistry,
) -> AsyncIterator[ChannelFactory]:
    """Factory that creates webhook notification channels via the SDK.

    Yields a factory callable and deletes all created channels on teardown.
    """
    created_ids: list[uuid.UUID] = []

    async def _create(**overrides: Any) -> CreateNotificationChannelResponse:
        defaults: dict[str, Any] = {
            "name": f"test-channel-{uuid.uuid4().hex[:8]}",
            "description": "Integration test channel",
            "channel_type": NotificationChannelType.WEBHOOK,
            "spec": WebhookSpec(url="https://example.com/webhook"),
            "enabled": True,
        }
        defaults.update(overrides)
        resp = await admin_registry.notification.create_channel(
            CreateNotificationChannelRequest(**defaults),
        )
        created_ids.append(resp.channel.id)
        return resp

    yield _create

    for cid in reversed(created_ids):
        try:
            await admin_registry.notification.delete_channel(cid)
        except Exception:
            pass


@pytest.fixture()
async def rule_factory(
    admin_registry: BackendAIClientRegistry,
    channel_factory: ChannelFactory,
) -> AsyncIterator[RuleFactory]:
    """Factory that creates notification rules via the SDK.

    Automatically creates a backing channel if channel_id is not provided.
    Yields a factory callable and deletes all created rules on teardown.
    """
    created_ids: list[uuid.UUID] = []

    async def _create(**overrides: Any) -> CreateNotificationRuleResponse:
        if "channel_id" not in overrides:
            ch = await channel_factory()
            overrides["channel_id"] = ch.channel.id
        defaults: dict[str, Any] = {
            "name": f"test-rule-{uuid.uuid4().hex[:8]}",
            "description": "Integration test rule",
            "rule_type": NotificationRuleType.SESSION_STARTED,
            "message_template": "Session {{ session_name }} started",
            "enabled": True,
        }
        defaults.update(overrides)
        resp = await admin_registry.notification.create_rule(
            CreateNotificationRuleRequest(**defaults),
        )
        created_ids.append(resp.rule.id)
        return resp

    yield _create

    for rid in reversed(created_ids):
        try:
            await admin_registry.notification.delete_rule(rid)
        except Exception:
            pass
