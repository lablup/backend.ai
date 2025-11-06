from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ai.backend.common.events.event_types.notification import NotificationTriggeredEvent
from ai.backend.common.logging import BraceStyleAdapter

from ...data.notification import NotificationRuleType
from ...services.notification.actions import ProcessNotificationAction

if TYPE_CHECKING:
    from ...services.notification.processors import NotificationProcessors

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

__all__ = ("NotificationEventHandler",)


class NotificationEventHandler:
    """
    Event handler for notification events.

    Receives NotificationTriggeredEvent anycast events and delegates
    processing to NotificationProcessors.
    """

    _processors: NotificationProcessors

    def __init__(
        self,
        processors: NotificationProcessors,
    ) -> None:
        self._processors = processors

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
        # Delegate to processor for business logic
        await self._processors.process_notification.wait_for_complete(
            ProcessNotificationAction(
                rule_type=NotificationRuleType(event.rule_type),
                timestamp=event.timestamp,
                notification_data=event.notification_data,
            )
        )
