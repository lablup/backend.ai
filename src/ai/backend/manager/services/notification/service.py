from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

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
    ValidateChannelAction,
    ValidateChannelActionResult,
    ValidateRuleAction,
    ValidateRuleActionResult,
)

if TYPE_CHECKING:
    from ai.backend.manager.data.notification.types import NotificationRuleData

    from ...repositories.notification import NotificationRepository

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

__all__ = ("NotificationService",)


@dataclass
class _ProcessedNotificationResult:
    """Internal result of processing notification rules."""

    rules_matched: int
    rules_processed: int


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
        result = await self._process_notification(
            rule_type=action.rule_type,
            timestamp=action.timestamp,
            notification_data=action.notification_data,
        )

        return ProcessNotificationActionResult(
            rule_type=action.rule_type,
            rules_matched=result.rules_matched,
            rules_processed=result.rules_processed,
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

    async def validate_channel(
        self,
        action: ValidateChannelAction,
    ) -> ValidateChannelActionResult:
        """Validates a notification channel by sending a test webhook."""
        try:
            # Verify the channel exists
            channel_data = await self._repository.get_channel_by_id(action.channel_id)

            # TODO: Implement ABC-based notification handler to actually send webhook
            # For now, just verify the channel configuration is valid
            log.info(
                "Validating notification channel '{}' (ID: {})",
                channel_data.name,
                action.channel_id,
            )

            return ValidateChannelActionResult(
                success=True,
                message=f"Channel '{channel_data.name}' configuration is valid. "
                f"(Actual webhook sending will be implemented with ABC-based handlers)",
            )

        except Exception as e:
            log.error("Failed to validate notification channel: {}", e)
            return ValidateChannelActionResult(
                success=False,
                message=f"Failed to validate notification channel: {str(e)}",
            )

    async def validate_rule(
        self,
        action: ValidateRuleAction,
    ) -> ValidateRuleActionResult:
        """Validates a notification rule by rendering its template with test data."""
        try:
            # Fetch the rule
            rule_data = await self._repository.get_rule_by_id(action.rule_id)

            # Render the template with test data
            try:
                template = self._template_env.from_string(rule_data.message_template)
                rendered_message = template.render(action.notification_data)

                return ValidateRuleActionResult(
                    success=True,
                    message=f"Rule '{rule_data.name}' template rendered successfully",
                    rendered_message=rendered_message,
                )

            except jinja2.TemplateError as template_error:
                log.warning(
                    "Failed to render template for rule '{}': {}",
                    rule_data.name,
                    template_error,
                )
                return ValidateRuleActionResult(
                    success=False,
                    message=f"Template rendering failed: {str(template_error)}",
                    rendered_message="",
                )

        except Exception as e:
            log.error("Failed to validate notification rule: {}", e)
            return ValidateRuleActionResult(
                success=False,
                message=f"Failed to validate notification rule: {str(e)}",
                rendered_message="",
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

    async def _process_notification(
        self,
        rule_type: NotificationRuleType,
        timestamp: datetime,
        notification_data: Mapping[str, Any],
        channel_id_filter: UUID | None = None,
        is_test: bool = False,
        channel_name: str | None = None,
    ) -> _ProcessedNotificationResult:
        """
        Query matching rules and process them.

        Args:
            rule_type: Type of notification rule
            timestamp: Timestamp of the notification
            notification_data: Data for template rendering
            channel_id_filter: Optional channel ID to filter rules
            is_test: Whether this is a test notification
            channel_name: Channel name (for test logging)

        Returns:
            Processed notification result
        """
        # Query matching rules
        all_rules = await self._repository.get_matching_rules(
            rule_type,
            enabled_only=True,
        )

        # Filter by channel if specified
        if channel_id_filter is not None:
            rules = [rule for rule in all_rules if rule.channel.id == channel_id_filter]
        else:
            rules = all_rules

        if not rules:
            if is_test:
                log.warning(
                    "No matching rules found for test notification",
                    channel_id=channel_id_filter,
                    rule_type=rule_type,
                )
            else:
                log.debug("No matching rules found", rule_type=rule_type)
            return _ProcessedNotificationResult(rules_matched=0, rules_processed=0)

        # Process rules
        rules_processed = self._process_rules(
            rules=rules,
            rule_type=rule_type,
            timestamp=timestamp,
            notification_data=notification_data,
            is_test=is_test,
            channel_id=channel_id_filter,
            channel_name=channel_name,
        )

        return _ProcessedNotificationResult(
            rules_matched=len(rules),
            rules_processed=rules_processed,
        )

    def _process_rules(
        self,
        rules: Sequence[NotificationRuleData],
        rule_type: NotificationRuleType,
        timestamp: datetime,
        notification_data: Mapping[str, Any],
        is_test: bool = False,
        channel_id: UUID | None = None,
        channel_name: str | None = None,
    ) -> int:
        """
        Process notification rules with template rendering.

        Args:
            rules: List of notification rules to process
            rule_type: Type of notification rule
            timestamp: Timestamp of the notification
            notification_data: Data for template rendering
            is_test: Whether this is a test notification
            channel_id: Channel ID (for test logging)
            channel_name: Channel name (for test logging)

        Returns:
            Number of successfully processed rules
        """
        rules_processed = 0

        for rule in rules:
            try:
                # Render message template
                self._render_template(
                    rule.message_template,
                    rule_type,
                    timestamp,
                    notification_data,
                )

                # TODO Phase 3: Send via handler
                # handler = self._handler_registry.get_handler(rule.channel.channel_type)
                # result = await handler.send(action, rule.channel.config)
                rules_processed += 1

                if is_test:
                    log.info(
                        "Test notification processed for rule",
                        rule_id=rule.id,
                        rule_name=rule.name,
                        channel_id=channel_id,
                        channel_name=channel_name,
                    )

            except Exception as e:
                log.error(
                    "Failed to process notification",
                    rule_type=rule_type,
                    rule_id=rule.id,
                    exc_info=e,
                )

        return rules_processed

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
