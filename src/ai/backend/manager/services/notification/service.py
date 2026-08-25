from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from ai.backend.common.data.notification import NotifiableMessage, NotificationRuleType
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.notification.types import MatchingNotificationRuleData
from ai.backend.manager.notification.types import ProcessRuleParams

from .actions import (
    ProcessNotificationAction,
    ProcessNotificationActionResult,
    ValidateChannelAction,
    ValidateChannelActionResult,
    ValidateRuleAction,
    ValidateRuleActionResult,
)
from .actions.process_notification import ProcessedRuleSuccess

if TYPE_CHECKING:
    from ai.backend.manager.notification import NotificationCenter
    from ai.backend.manager.repositories.notification import NotificationRepository

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

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
        # Fetch the rule to know its rule_type, then the channel it names. The rule
        # carries the channel's id, not the channel — reading both is this method's
        # job rather than the row conversion's.
        rule = await self._repository.get_rule_by_id(action.rule_id)
        channel = await self._repository.get_channel_by_id(rule.channel_id)

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
                channel=channel,
                timestamp=datetime.now(UTC),
                notification_data=validated_data,
            )
        )
        return ValidateRuleActionResult(
            message=result.message,
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
        matches = await self._repository.get_matching_rules(
            rule_type,
            enabled_only=True,
        )
        if not matches:
            return _ProcessedNotificationResult(
                rules_matched=0,
                successes=[],
                errors=[],
            )
        # Process rules
        result = await self._process_rules(
            matches=matches,
            timestamp=timestamp,
            notification_data=notification_data,
        )
        return _ProcessedNotificationResult(
            rules_matched=len(matches),
            successes=result.successes,
            errors=result.errors,
        )

    async def _process_rules(
        self,
        matches: Sequence[MatchingNotificationRuleData],
        timestamp: datetime,
        notification_data: NotifiableMessage,
    ) -> _ProcessedRulesResult:
        """
        Process notification rules concurrently.

        Args:
            matches: Rules paired with the channel each dispatches through
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
                        message_template=match.rule.message_template,
                        rule_type=match.rule.rule_type,
                        channel=match.channel,
                        timestamp=timestamp,
                        notification_data=notification_data,
                    )
                )
                for match in matches
            ],
            return_exceptions=True,
        )

        # Collect successes and failures
        successes: list[ProcessedRuleSuccess] = []
        errors: list[BaseException] = []

        for match, result in zip(matches, results, strict=True):
            if isinstance(result, BaseException):
                errors.append(result)
                log.error(
                    "Failed to process notification for rule '{}': {}",
                    match.rule.name,
                    str(result),
                )
                continue
            successes.append(
                ProcessedRuleSuccess(
                    rule_id=match.rule.id,
                    rule_name=match.rule.name,
                    channel_name=match.channel.name,
                )
            )
            log.debug(
                "Notification sent successfully for rule '{}' (channel: '{}')",
                match.rule.name,
                match.channel.name,
                rule_id=match.rule.id,
            )

        return _ProcessedRulesResult(
            successes=successes,
            errors=errors,
        )
