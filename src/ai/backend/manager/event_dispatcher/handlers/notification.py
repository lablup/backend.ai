from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable

from ai.backend.common.data.notification import NotifiableMessage
from ai.backend.common.events.event_types.notification import NotificationTriggeredEvent
from ai.backend.logging import BraceStyleAdapter

from ...data.notification import NotificationRuleType
from ...services.notification.actions import ProcessNotificationAction

if TYPE_CHECKING:
    from ...services.processors import Processors

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

__all__ = ("NotificationEventHandler",)


class NotificationEventHandler:
    """
    Event handler for notification events.

    Receives NotificationTriggeredEvent anycast events and delegates
    processing to NotificationProcessors.
    """

    _processors_factory: Callable[[], Processors]

    def __init__(
        self,
        processors_factory: Callable[[], Processors],
    ) -> None:
        self._processors_factory = processors_factory

    async def handle_notification_triggered(
        self,
        context: None,
        source: str,
        event: NotificationTriggeredEvent,
    ) -> None:
        """
        Handle NotificationTriggeredEvent by delegating to the processor.

        Args:
            context: Event context (unused for notifications)
            source: Event source identifier
            event: NotificationTriggeredEvent containing notification data
        """
        log.info(
            "Received notification event: {0} from {1}",
            event.rule_type,
            source,
        )

        # Validate notification_data against the rule type's schema
        rule_type = NotificationRuleType(event.rule_type)
        try:
            validated_data = NotifiableMessage.validate_notification_data(
                rule_type=rule_type,
                data=event.notification_data,
            )
        except Exception as e:
            log.error(
                "Failed to validate notification data for rule type {0}: {1}",
                event.rule_type,
                str(e),
            )
            # Re-raise to let the caller know validation failed
            raise

        # Delegate to processor for business logic
        processors = self._processors_factory()
        await processors.notification.process_notification.wait_for_complete(
            ProcessNotificationAction(
                rule_type=rule_type,
                timestamp=event.timestamp,
                notification_data=validated_data,
            )
        )
