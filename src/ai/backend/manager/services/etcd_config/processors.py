from __future__ import annotations

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec

from .actions.delete_config import DeleteConfigAction, DeleteConfigActionResult
from .actions.get_config import GetConfigAction, GetConfigActionResult
from .actions.get_resource_metadata import (
    GetResourceMetadataAction,
    GetResourceMetadataActionResult,
)
from .actions.get_resource_slots import GetResourceSlotsAction, GetResourceSlotsActionResult
from .actions.get_vfolder_types import GetVfolderTypesAction, GetVfolderTypesActionResult
from .actions.set_config import SetConfigAction, SetConfigActionResult
from .service import EtcdConfigService

__all__ = ("EtcdConfigProcessors",)


class EtcdConfigProcessors(AbstractProcessorPackage):
    """Processor package for etcd config operations."""

    get_resource_slots: ActionProcessor[GetResourceSlotsAction, GetResourceSlotsActionResult]
    get_resource_metadata: ActionProcessor[
        GetResourceMetadataAction, GetResourceMetadataActionResult
    ]
    get_vfolder_types: ActionProcessor[GetVfolderTypesAction, GetVfolderTypesActionResult]
    get_config: ActionProcessor[GetConfigAction, GetConfigActionResult]
    set_config: ActionProcessor[SetConfigAction, SetConfigActionResult]
    delete_config: ActionProcessor[DeleteConfigAction, DeleteConfigActionResult]

    def __init__(self, service: EtcdConfigService, action_monitors: list[ActionMonitor]) -> None:
        self.get_resource_slots = ActionProcessor(service.get_resource_slots, action_monitors)
        self.get_resource_metadata = ActionProcessor(service.get_resource_metadata, action_monitors)
        self.get_vfolder_types = ActionProcessor(service.get_vfolder_types, action_monitors)
        self.get_config = ActionProcessor(service.get_config, action_monitors)
        self.set_config = ActionProcessor(service.set_config, action_monitors)
        self.delete_config = ActionProcessor(service.delete_config, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            GetResourceSlotsAction.spec(),
            GetResourceMetadataAction.spec(),
            GetVfolderTypesAction.spec(),
            GetConfigAction.spec(),
            SetConfigAction.spec(),
            DeleteConfigAction.spec(),
        ]
