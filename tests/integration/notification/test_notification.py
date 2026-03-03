from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

import pytest

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.data.notification.types import NotificationRuleType
from ai.backend.common.dto.manager.notification import (
    CreateNotificationChannelResponse,
    CreateNotificationRuleResponse,
    DeleteNotificationChannelResponse,
    DeleteNotificationRuleResponse,
    GetNotificationChannelResponse,
    GetNotificationRuleResponse,
    ListNotificationChannelsResponse,
    ListNotificationRulesResponse,
    SearchNotificationChannelsRequest,
    SearchNotificationRulesRequest,
    UpdateNotificationChannelRequest,
    UpdateNotificationChannelResponse,
    UpdateNotificationRuleRequest,
    UpdateNotificationRuleResponse,
)

ChannelFactory = Callable[..., Coroutine[Any, Any, CreateNotificationChannelResponse]]
RuleFactory = Callable[..., Coroutine[Any, Any, CreateNotificationRuleResponse]]


@pytest.mark.integration
class TestChannelLifecycle:
    async def test_channel_crud_lifecycle(
        self,
        admin_registry: BackendAIClientRegistry,
        channel_factory: ChannelFactory,
    ) -> None:
        """create -> get -> update -> search -> delete."""
        # 1. Create
        created = await channel_factory(name="lifecycle-channel")
        channel_id = created.channel.id
        assert created.channel.name == "lifecycle-channel"

        # 2. Get
        got = await admin_registry.notification.get_channel(channel_id)
        assert isinstance(got, GetNotificationChannelResponse)
        assert got.channel.id == channel_id

        # 3. Update
        updated = await admin_registry.notification.update_channel(
            channel_id,
            UpdateNotificationChannelRequest(name="lifecycle-channel-updated"),
        )
        assert isinstance(updated, UpdateNotificationChannelResponse)
        assert updated.channel.name == "lifecycle-channel-updated"

        # 4. Search
        searched = await admin_registry.notification.search_channels(
            SearchNotificationChannelsRequest(),
        )
        assert isinstance(searched, ListNotificationChannelsResponse)
        ids = [ch.id for ch in searched.channels]
        assert channel_id in ids

        # 5. Delete
        deleted = await admin_registry.notification.delete_channel(channel_id)
        assert isinstance(deleted, DeleteNotificationChannelResponse)
        assert deleted.deleted is True


@pytest.mark.integration
class TestRuleLifecycle:
    async def test_rule_crud_lifecycle(
        self,
        admin_registry: BackendAIClientRegistry,
        channel_factory: ChannelFactory,
        rule_factory: RuleFactory,
    ) -> None:
        """create_channel -> create_rule -> get -> update -> search -> delete_rule -> delete_channel."""
        # 1. Create channel
        ch = await channel_factory(name="rule-lifecycle-channel")
        channel_id = ch.channel.id

        # 2. Create rule
        created = await rule_factory(
            name="lifecycle-rule",
            channel_id=channel_id,
            rule_type=NotificationRuleType.SESSION_TERMINATED,
            message_template="Session {{ session_name }} terminated",
        )
        rule_id = created.rule.id
        assert created.rule.name == "lifecycle-rule"

        # 3. Get
        got = await admin_registry.notification.get_rule(rule_id)
        assert isinstance(got, GetNotificationRuleResponse)
        assert got.rule.id == rule_id

        # 4. Update
        updated = await admin_registry.notification.update_rule(
            rule_id,
            UpdateNotificationRuleRequest(name="lifecycle-rule-updated"),
        )
        assert isinstance(updated, UpdateNotificationRuleResponse)
        assert updated.rule.name == "lifecycle-rule-updated"

        # 5. Search
        searched = await admin_registry.notification.search_rules(
            SearchNotificationRulesRequest(),
        )
        assert isinstance(searched, ListNotificationRulesResponse)
        ids = [r.id for r in searched.rules]
        assert rule_id in ids

        # 6. Delete rule
        deleted_rule = await admin_registry.notification.delete_rule(rule_id)
        assert isinstance(deleted_rule, DeleteNotificationRuleResponse)
        assert deleted_rule.deleted is True

        # 7. Delete channel
        deleted_ch = await admin_registry.notification.delete_channel(channel_id)
        assert isinstance(deleted_ch, DeleteNotificationChannelResponse)
        assert deleted_ch.deleted is True
