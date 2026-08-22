from __future__ import annotations

from typing import Any

from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import (
    GlobalActionProcessor,
    PublicActionProcessor,
)
from ai.backend.manager.services.etcd_config.actions.delete_config import (
    DeleteConfigAction,
    DeleteConfigActionResult,
)
from ai.backend.manager.services.etcd_config.actions.get_config import (
    GetConfigAction,
    GetConfigActionResult,
)
from ai.backend.manager.services.etcd_config.actions.get_resource_metadata import (
    GetResourceMetadataAction,
    GetResourceMetadataActionResult,
)
from ai.backend.manager.services.etcd_config.actions.get_resource_slots import (
    GetResourceSlotsAction,
    GetResourceSlotsActionResult,
)
from ai.backend.manager.services.etcd_config.actions.get_vfolder_types import (
    GetVfolderTypesAction,
    GetVfolderTypesActionResult,
)
from ai.backend.manager.services.etcd_config.actions.set_config import (
    SetConfigAction,
    SetConfigActionResult,
)
from ai.backend.manager.services.etcd_config.service import EtcdConfigService


class EtcdConfigProcessors:
    """The installation's own configuration, read from etcd and the config provider.

    Every operation reaches an external store, so the service stays and only the action
    shapes moved. What the config describes belongs to no entity, so all six are global;
    the three that report what the installation offers are open to any authenticated
    caller, while reading and writing raw keys stays behind the SUPERADMIN gate.
    """

    get_resource_slots: PublicActionProcessor[GetResourceSlotsAction, GetResourceSlotsActionResult]
    get_resource_metadata: PublicActionProcessor[
        GetResourceMetadataAction, GetResourceMetadataActionResult
    ]
    get_vfolder_types: PublicActionProcessor[GetVfolderTypesAction, GetVfolderTypesActionResult]
    get_config: GlobalActionProcessor[GetConfigAction, GetConfigActionResult]
    set_config: GlobalActionProcessor[SetConfigAction, SetConfigActionResult]
    delete_config: GlobalActionProcessor[DeleteConfigAction, DeleteConfigActionResult]

    def __init__(self, group: ProcessorGroup[Any], service: EtcdConfigService) -> None:
        self.get_resource_slots = group.public(GetResourceSlotsAction, service.get_resource_slots)
        self.get_resource_metadata = group.public(
            GetResourceMetadataAction, service.get_resource_metadata
        )
        self.get_vfolder_types = group.public(GetVfolderTypesAction, service.get_vfolder_types)
        self.get_config = group.global_scope(GetConfigAction, service.get_config)
        self.set_config = group.global_scope(SetConfigAction, service.set_config)
        self.delete_config = group.global_scope(DeleteConfigAction, service.delete_config)
