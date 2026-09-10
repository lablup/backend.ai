from typing import override

from aiohttp import web

from ai.backend.common.data.entity.container_registry import ContainerRegistryEntityType
from ai.backend.common.exception import ErrorDetail
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityError, EntityErrorCode


class InvalidContainerRegistryProjectOnCreate(EntityError, web.HTTPBadRequest):
    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ContainerRegistryEntityType(), ActionOperationType.CREATE, ErrorDetail.BAD_REQUEST
        )


class InvalidContainerRegistryProjectOnModify(EntityError, web.HTTPBadRequest):
    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ContainerRegistryEntityType(), ActionOperationType.UPDATE, ErrorDetail.BAD_REQUEST
        )


class InvalidContainerRegistryURL(EntityError, web.HTTPBadRequest):
    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ContainerRegistryEntityType(), ActionOperationType.CREATE, ErrorDetail.BAD_REQUEST
        )
