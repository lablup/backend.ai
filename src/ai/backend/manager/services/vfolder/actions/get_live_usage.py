"""V2 live-usage action — fetches usage statistics through the storage proxy on demand."""

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.action.single_entity import BaseSingleEntityActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.vfolder.types import VFolderLiveUsageData
from ai.backend.manager.services.vfolder.actions.base import VFolderSingleEntityAction


@dataclass
class GetVFolderLiveUsageAction(VFolderSingleEntityAction):
    vfolder_uuid: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_uuid)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def target_entity_id(self) -> str:
        return str(self.vfolder_uuid)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.VFOLDER,
            element_id=str(self.vfolder_uuid),
        )


@dataclass
class GetVFolderLiveUsageActionResult(BaseSingleEntityActionResult):
    vfolder_uuid: uuid.UUID
    usage: VFolderLiveUsageData | None

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_uuid)

    @override
    def target_entity_id(self) -> str:
        return str(self.vfolder_uuid)
