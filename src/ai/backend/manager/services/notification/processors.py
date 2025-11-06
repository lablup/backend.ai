from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec

from .actions import ProcessNotificationAction, ProcessNotificationActionResult
from .service import NotificationService


class NotificationProcessors(AbstractProcessorPackage):
    """Processor package for notification operations."""

    process_notification: ActionProcessor[
        ProcessNotificationAction, ProcessNotificationActionResult
    ]

    def __init__(self, service: NotificationService, action_monitors: list[ActionMonitor]) -> None:
        self.process_notification = ActionProcessor(service.process_notification, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            ProcessNotificationAction.spec(),
        ]
