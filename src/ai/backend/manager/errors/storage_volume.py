from __future__ import annotations

from typing import override

from ai.backend.common.data.entity.storage_volume import StorageVolumeEntityType
from ai.backend.common.exception import ErrorDetail
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityError, EntityErrorCode

from .common import ObjectNotFound


class StorageVolumeHoldingNotFound(EntityError, ObjectNotFound):
    object_name = "storage_volume_holding"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            StorageVolumeEntityType(), ActionOperationType.UPDATE, ErrorDetail.NOT_FOUND
        )
