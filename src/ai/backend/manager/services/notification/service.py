from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, cast

from ai.backend.common.data.notification import NotifiableMessage
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.notification import NotificationRuleType
from ai.backend.manager.notification.types import ProcessRuleParams
from ai.backend.manager.repositories.notification.creators import NotificationRuleCreatorSpec
from ai.backend.manager.repositories.notification.updaters import NotificationRuleUpdaterSpec

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
    ProcessedRuleSuccess,
    ProcessNotificationAction,
    ProcessNotificationActionResult,
    SearchChannelsAction,
    SearchChannelsActionResult,
    SearchRulesAction,
    SearchRulesActionResult,
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
    from ai.backend.manager.notification import NotificationCenter

    from ...repositories.notification import NotificationRepository

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

__all__ = ("NotificationService",)


@dataclass
class _ProcessedRulesResult:
    """Internal result of processing notification rules."""

    successes: list[ProcessedRuleSuccess]
    errors: list[BaseException]


@dataclass
class _ProcessedNotificationResult:
    """Internal result of processing notification rules."""

    rules_matched: int
    successes: list[ProcessedRuleSuccess]
    errors: list[BaseException]


class NotificationService:
    """
    Service for processing notification events.
    Handles rule matching, template rendering, and notification preparation.
    """

    _repository: NotificationRepository
    _notification_center: NotificationCenter

    def __init__(
        self,
        repository: NotificationRepository,
        notification_center: NotificationCenter,
    ) -> None:
        self._repository = repository
        self._notification_center = notification_center

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
            successes=result.successes,
            errors=result.errors,
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
        spec = cast(NotificationRuleCreatorSpec, action.creator.spec)
        # Validate message_template length
        if len(spec.message_template) > 65536:
            raise ValueError("message_template must not exceed 65536 characters (64KB)")

        rule_data = await self._repository.create_rule(action.creator)

        return CreateRuleActionResult(
            rule_data=rule_data,
        )

    async def update_channel(
        self,
        action: UpdateChannelAction,
    ) -> UpdateChannelActionResult:
        """Updates an existing notification channel."""
        channel_data = await self._repository.update_channel(updater=action.updater)

        return UpdateChannelActionResult(
            channel_data=channel_data,
        )

    async def update_rule(
        self,
        action: UpdateRuleAction,
    ) -> UpdateRuleActionResult:
        """Updates an existing notification rule."""
        # Validate message_template length if being updated
        spec = cast(NotificationRuleUpdaterSpec, action.updater.spec)
        if (message_template := spec.message_template.optional_value()) is not None:
            if len(message_template) > 65536:
                raise ValueError("message_template must not exceed 65536 characters (64KB)")

        rule_data = await self._repository.update_rule(updater=action.updater)

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
        """
        Validates a notification channel by sending a test message.

        Raises:
            NotificationChannelNotFound: If the channel does not exist
            NotificationProcessingFailure: If sending the test message fails
        """
        channel_data = await self._repository.get_channel_by_id(action.channel_id)
        await self._notification_center.validate_channel(channel_data, action.test_message)
        log.debug(
            "Test notification sent successfully for channel '{}' (ID: {})",
            channel_data.name,
            action.channel_id,
        )

        return ValidateChannelActionResult()

    async def validate_rule(
        self,
        action: ValidateRuleAction,
    ) -> ValidateRuleActionResult:
        """
        Validates a notification rule by rendering its template with test data.

        Raises:
            NotificationRuleNotFound: If the rule does not exist
            NotificationTemplateRenderingFailure: If template rendering fails
            ValidationError: If notification_data doesn't match the rule type's schema
        """
        from ai.backend.common.data.notification import NotifiableMessage

        # Fetch the rule to know its rule_type
        rule = await self._repository.get_rule_by_id(action.rule_id)

        # Validate notification_data against the rule type's schema
        validated_data = NotifiableMessage.validate_notification_data(
            rule_type=rule.rule_type,
            data=action.notification_data,
        )

        # Process the rule with validated data
        result = await self._notification_center.process_rule(
            ProcessRuleParams(
                message_template=rule.message_template,
                rule_type=rule.rule_type,
                channel=rule.channel,
                timestamp=datetime.now(),
                notification_data=validated_data,
            )
        )
        return ValidateRuleActionResult(
            message=result.message,
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

    async def search_channels(
        self,
        action: SearchChannelsAction,
    ) -> SearchChannelsActionResult:
        """Searches notification channels."""
        result = await self._repository.search_channels(
            querier=action.querier,
        )

        return SearchChannelsActionResult(
            channels=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def search_rules(
        self,
        action: SearchRulesAction,
    ) -> SearchRulesActionResult:
        """Searches notification rules."""
        result = await self._repository.search_rules(
            querier=action.querier,
        )
        return SearchRulesActionResult(
            rules=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def _process_notification(
        self,
        rule_type: NotificationRuleType,
        timestamp: datetime,
        notification_data: NotifiableMessage,
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
        rules = await self._repository.get_matching_rules(
            rule_type,
            enabled_only=True,
        )
        if not rules:
            return _ProcessedNotificationResult(
                rules_matched=0,
                successes=[],
                errors=[],
            )
        # Process rules
        result = await self._process_rules(
            rules=rules,
            timestamp=timestamp,
            notification_data=notification_data,
        )
        return _ProcessedNotificationResult(
            rules_matched=len(rules),
            successes=result.successes,
            errors=result.errors,
        )

    async def _process_rules(
        self,
        rules: Sequence[NotificationRuleData],
        timestamp: datetime,
        notification_data: NotifiableMessage,
    ) -> _ProcessedRulesResult:
        """
        Process notification rules concurrently.

        Args:
            rules: List of notification rules to process
            rule_type: Type of notification rule
            timestamp: Timestamp of the notification
            notification_data: Data for template rendering

        Returns:
            ProcessedRulesResult containing successes and errors lists
        """
        # Process all rules concurrently with return_exceptions=True for partial failure tolerance
        results = await asyncio.gather(
            *[
                self._notification_center.process_rule(
                    ProcessRuleParams(
                        message_template=rule.message_template,
                        rule_type=rule.rule_type,
                        channel=rule.channel,
                        timestamp=timestamp,
                        notification_data=notification_data,
                    )
                )
                for rule in rules
            ],
            return_exceptions=True,
        )

        # Collect successes and failures
        successes: list[ProcessedRuleSuccess] = []
        errors: list[BaseException] = []

        for rule, result in zip(rules, results):
            if isinstance(result, BaseException):
                errors.append(result)
                log.error(
                    "Failed to process notification for rule '{}': {}",
                    rule.name,
                    str(result),
                )
                continue
            successes.append(
                ProcessedRuleSuccess(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    channel_name=rule.channel.name,
                )
            )
            log.debug(
                "Notification sent successfully for rule '{}' (channel: '{}')",
                rule.name,
                rule.channel.name,
                rule_id=rule.id,
            )

        return _ProcessedRulesResult(
            successes=successes,
            errors=errors,
        )
