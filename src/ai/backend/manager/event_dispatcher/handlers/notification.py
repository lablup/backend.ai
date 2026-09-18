from __future__ import annotations

import logging

from ai.backend.common.data.notification import NotifiableMessage, NotificationRuleType
from ai.backend.common.events.event_types.notification import NotificationTriggeredEvent
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.services.notification.actions import ProcessNotificationAction
from ai.backend.manager.services.notification.service import NotificationService

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("NotificationEventHandler",)


class NotificationEventHandler:
    """
    Event handler for notification events.

    Receives NotificationTriggeredEvent anycast events and delegates
    processing to NotificationService.
    """

    _notification_service: NotificationService

    def __init__(
        self,
        notification_service: NotificationService,
    ) -> None:
        self._notification_service = notification_service

    async def handle_notification_triggered(
        self,
        _context: None,
        source: str,
        event: NotificationTriggeredEvent,
    ) -> None:
        """
        Handle NotificationTriggeredEvent by delegating to the service.

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

        # Delegate to service for business logic
        # TODO(BA-7978): Move the logic out of the service and call repositories/clients directly.
        await self._notification_service.process_notification(
            ProcessNotificationAction(
                rule_type=rule_type,
                timestamp=event.timestamp,
                notification_data=validated_data,
            )
        )
