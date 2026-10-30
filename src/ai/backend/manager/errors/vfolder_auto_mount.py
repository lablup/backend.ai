from typing import override

from aiohttp import web

from ai.backend.common.data.entity.vfolder_auto_mount import VFolderAutoMountEntityType
from ai.backend.common.exception import ErrorDetail
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityError, EntityErrorCode


class VFolderAutoMountAlreadyExists(EntityError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/vfolder-auto-mount-already-exists"
    error_title = "The vfolder or the mount destination is already auto-mounted in the scope."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            VFolderAutoMountEntityType(), ActionOperationType.CREATE, ErrorDetail.ALREADY_EXISTS
        )


class VFolderAutoMountVFolderOutsideScope(EntityError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/vfolder-auto-mount-vfolder-outside-scope"
    error_title = "The vfolder does not belong to the project or user it is to be auto-mounted in."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            VFolderAutoMountEntityType(),
            ActionOperationType.CREATE,
            ErrorDetail.INVALID_PARAMETERS,
        )


class VFolderAutoMountDestinationInUse(EntityError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/vfolder-auto-mount-destination-in-use"
    error_title = "Another auto-mount in the scope already uses the mount destination."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            VFolderAutoMountEntityType(), ActionOperationType.UPDATE, ErrorDetail.ALREADY_EXISTS
        )
