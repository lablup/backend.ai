import uuid
from typing import Optional

from ai.backend.manager.actions.action import BaseAction, BaseActionResult, BaseBatchAction


class VFolderAction(BaseAction):
    def entity_type(self):
        return "vfolder"


class VFolderBatchAction(BaseBatchAction):
    def entity_type(self):
        return "vfolder"


class CreateVFolderAction(VFolderAction):
    def entity_id(self):
        return None

    def operation_type(self):
        return "create"


class CreateVFolderActionResult(BaseActionResult):
    vfolder_id: uuid.UUID

    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_id)


class UpdateVFolderAttributeAction(VFolderAction):
    pass


class UpdateVFolderAttributeActionResult(BaseActionResult):
    pass


class ChangeOwnershipAction(VFolderAction):
    pass


class ChangeOwnershipActionResult(BaseActionResult):
    pass


class ListVFolderAction(VFolderAction):
    pass


class ListVFolderActionResult(BaseActionResult):
    pass


class MoveToTrashVFolderAction(VFolderAction):
    pass


class MoveToTrashVFolderActionResult(BaseActionResult):
    pass


class RestoreVFolderFromTrashAction(VFolderAction):
    pass


class RestoreVFolderFromTrashActionResult(BaseActionResult):
    pass


class DeleteForeverVFolderAction(VFolderAction):
    pass


class DeleteForeverVFolderActionResult(BaseActionResult):
    pass


class PurgeVFolderAction(VFolderAction):
    """
    This action transits the state of vfolder from ready to delete-forever directly.
    """


class PurgeVFolderActionResult(BaseActionResult):
    pass


class CloneVFolderAction(VFolderAction):
    pass


class CloneVFolderActionResult(BaseActionResult):
    pass
