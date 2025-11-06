from __future__ import annotations

import logging
from collections.abc import Mapping
from datetime import datetime
from typing import TYPE_CHECKING, Any

import jinja2

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.manager.data.notification import NotificationRuleType

from .actions import (
    CreateChannelAction,
    CreateChannelActionResult,
    CreateRuleAction,
    CreateRuleActionResult,
    DeleteChannelAction,
    DeleteChannelActionResult,
    DeleteRuleAction,
    DeleteRuleActionResult,
    GetChannelAction,
    GetChannelActionResult,
    GetRuleAction,
    GetRuleActionResult,
    ListChannelsAction,
    ListChannelsActionResult,
    ListRulesAction,
    ListRulesActionResult,
    ProcessNotificationAction,
    ProcessNotificationActionResult,
    UpdateChannelAction,
    UpdateChannelActionResult,
    UpdateRuleAction,
    UpdateRuleActionResult,
)

if TYPE_CHECKING:
    from ...repositories.notification import NotificationRepository

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

__all__ = ("NotificationService",)


class NotificationService:
    """
    Service for processing notification events.
    Handles rule matching, template rendering, and notification preparation.
    """

    _repository: NotificationRepository
    _template_env: jinja2.Environment

    def __init__(self, repository: NotificationRepository) -> None:
        self._repository = repository
        # Initialize Jinja2 environment for template rendering
        self._template_env = jinja2.Environment(
            loader=jinja2.BaseLoader(),
            autoescape=jinja2.select_autoescape(),
        )

    async def process_notification(
        self, action: ProcessNotificationAction
    ) -> ProcessNotificationActionResult:
        """
        Processes a notification event by finding matching rules
        and preparing messages (Phase 1-2: logging only).
        """
        # Query matching rules
        rules = await self._repository.get_matching_rules(
            action.rule_type,
            enabled_only=True,
        )

        if not rules:
            log.debug("No matching rules found", rule_type=action.rule_type)
            return ProcessNotificationActionResult(
                rule_type=action.rule_type,
                rules_matched=0,
                rules_processed=0,
            )

        rules_processed = 0
        # Process each matching rule
        for rule in rules:
            try:
                # Render message template
                self._render_template(
                    rule.message_template,
                    action.rule_type,
                    action.timestamp,
                    action.notification_data,
                )

                # TODO Phase 3: Send via handler
                # handler = self._handler_registry.get_handler(rule.channel.channel_type)
                # result = await handler.send(action, rule.channel.config)
                rules_processed += 1

            except Exception as e:
                log.error(
                    "Failed to process notification",
                    rule_type=action.rule_type,
                    rule_id=rule.id,
                    exc_info=e,
                )

        return ProcessNotificationActionResult(
            rule_type=action.rule_type,
            rules_matched=len(rules),
            rules_processed=rules_processed,
        )

    async def create_channel(
        self,
        action: CreateChannelAction,
    ) -> CreateChannelActionResult:
        """Creates a new notification channel."""
        channel_data = await self._repository.create_channel(action.creator)

        return CreateChannelActionResult(
            channel_data=channel_data,
        )

    async def create_rule(
        self,
        action: CreateRuleAction,
    ) -> CreateRuleActionResult:
        """Creates a new notification rule."""
        rule_data = await self._repository.create_rule(action.creator)

        return CreateRuleActionResult(
            rule_data=rule_data,
        )

    async def update_channel(
        self,
        action: UpdateChannelAction,
    ) -> UpdateChannelActionResult:
        """Updates an existing notification channel."""
        channel_data = await self._repository.update_channel(
            channel_id=action.channel_id,
            modifier=action.modifier,
        )

        return UpdateChannelActionResult(
            channel_data=channel_data,
        )

    async def update_rule(
        self,
        action: UpdateRuleAction,
    ) -> UpdateRuleActionResult:
        """Updates an existing notification rule."""
        rule_data = await self._repository.update_rule(
            rule_id=action.rule_id,
            modifier=action.modifier,
        )

        return UpdateRuleActionResult(
            rule_data=rule_data,
        )

    async def delete_channel(
        self,
        action: DeleteChannelAction,
    ) -> DeleteChannelActionResult:
        """Deletes a notification channel."""
        deleted = await self._repository.delete_channel(action.channel_id)

        return DeleteChannelActionResult(
            deleted=deleted,
        )

    async def delete_rule(
        self,
        action: DeleteRuleAction,
    ) -> DeleteRuleActionResult:
        """Deletes a notification rule."""
        deleted = await self._repository.delete_rule(action.rule_id)

        return DeleteRuleActionResult(
            deleted=deleted,
        )

    async def get_channel(
        self,
        action: GetChannelAction,
    ) -> GetChannelActionResult:
        """Gets a notification channel by ID."""
        channel_data = await self._repository.get_channel_by_id(action.channel_id)

        return GetChannelActionResult(
            channel_data=channel_data,
        )

    async def get_rule(
        self,
        action: GetRuleAction,
    ) -> GetRuleActionResult:
        """Gets a notification rule by ID."""
        rule_data = await self._repository.get_rule_by_id(action.rule_id)

        return GetRuleActionResult(
            rule_data=rule_data,
        )

    async def list_channels(
        self,
        action: ListChannelsAction,
    ) -> ListChannelsActionResult:
        """Lists all notification channels."""
        channels = await self._repository.list_channels(
            querier=action.querier,
        )

        return ListChannelsActionResult(
            channels=channels,
        )

    async def list_rules(
        self,
        action: ListRulesAction,
    ) -> ListRulesActionResult:
        """Lists all notification rules."""
        rules = await self._repository.list_rules(
            querier=action.querier,
        )

        return ListRulesActionResult(
            rules=rules,
        )

    def _render_template(
        self,
        template_str: str,
        rule_type: NotificationRuleType,
        timestamp: datetime,
        notification_data: Mapping[str, Any],
    ) -> str:
        """Renders a Jinja2 template with notification event data."""
        try:
            template = self._template_env.from_string(template_str)
            return template.render(
                rule_type=str(rule_type),
                timestamp=timestamp,
                data=notification_data,
                **notification_data,  # Allow direct access to data fields
            )
        except jinja2.TemplateError as e:
            log.error(
                "Failed to render notification template",
                template=template_str,
                error=str(e),
            )
            # Return a fallback message
            return f"Notification for {str(rule_type)}"
