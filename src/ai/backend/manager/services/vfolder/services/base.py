from dataclasses import dataclass

from ....models.utils import ExtendedAsyncSAEngine
from ....registry import AgentRegistry
from ..actions.base import (
    ChangeOwnershipAction,
    ChangeOwnershipActionResult,
    CloneVFolderAction,
    CloneVFolderActionResult,
    CreateVFolderAction,
    CreateVFolderActionResult,
    DeleteForeverVFolderAction,
    DeleteForeverVFolderActionResult,
    ListVFolderAction,
    ListVFolderActionResult,
    MoveToTrashVFolderAction,
    MoveToTrashVFolderActionResult,
    PurgeVFolderAction,
    PurgeVFolderActionResult,
    RestoreVFolderFromTrashAction,
    RestoreVFolderFromTrashActionResult,
    UpdateVFolderAttributeAction,
    UpdateVFolderAttributeActionResult,
)


@dataclass
class ServiceInitParameter:
    db: ExtendedAsyncSAEngine
    registry: AgentRegistry


class VFolderService:
    _db: ExtendedAsyncSAEngine
    _registry: AgentRegistry

    def __init__(self, parameter: ServiceInitParameter) -> None:
        self._db = parameter.db
        self._registry = parameter.registry

    async def create(self, action: CreateVFolderAction) -> CreateVFolderActionResult:
        pass

    async def update_attribute(
        self, action: UpdateVFolderAttributeAction
    ) -> UpdateVFolderAttributeActionResult:
        pass

    async def change_ownership(self, action: ChangeOwnershipAction) -> ChangeOwnershipActionResult:
        pass

    async def list(self, action: ListVFolderAction) -> ListVFolderActionResult:
        pass

    async def move_to_trash(
        self, action: MoveToTrashVFolderAction
    ) -> MoveToTrashVFolderActionResult:
        pass

    async def restore(
        self, action: RestoreVFolderFromTrashAction
    ) -> RestoreVFolderFromTrashActionResult:
        pass

    async def delete_forever(
        self, action: DeleteForeverVFolderAction
    ) -> DeleteForeverVFolderActionResult:
        pass

    async def purge(self, action: PurgeVFolderAction) -> PurgeVFolderActionResult:
        pass

    async def clone(self, action: CloneVFolderAction) -> CloneVFolderActionResult:
        pass
