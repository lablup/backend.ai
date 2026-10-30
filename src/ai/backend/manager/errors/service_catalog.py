from __future__ import annotations

from typing import override

from ai.backend.common.data.entity.service_catalog import ServiceCatalogEntityType
from ai.backend.common.exception import ErrorDetail
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityError, EntityErrorCode

from .common import ObjectNotFound


class ServiceCatalogNotFound(EntityError, ObjectNotFound):
    object_name = "service_catalog"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ServiceCatalogEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )
