from __future__ import annotations

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec

from .actions.sync_model_definitions import (
    SyncModelDefinitionsAction,
    SyncModelDefinitionsActionResult,
)
from .admin_service import DeploymentAdminService


class DeploymentAdminProcessors(AbstractProcessorPackage):
    """Processor package for admin-only deployment maintenance operations."""

    sync_model_definitions: ActionProcessor[
        SyncModelDefinitionsAction, SyncModelDefinitionsActionResult
    ]

    def __init__(
        self,
        service: DeploymentAdminService,
        action_monitors: list[ActionMonitor],
    ) -> None:
        self.sync_model_definitions = ActionProcessor(
            service.sync_model_definitions, action_monitors
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            SyncModelDefinitionsAction.spec(),
        ]
