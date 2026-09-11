from typing import override

from aiohttp import web

from ai.backend.common.data.entity.vfs_storage import VFSStorageEntityType
from ai.backend.common.exception import ErrorDetail
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityError, EntityErrorCode


class VFSStorageNotFoundError(EntityError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/vfs-storage-not-found"
    error_title = "VFS Storage Not Found"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            VFSStorageEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )
