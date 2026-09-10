from typing import override

from aiohttp import web

from ai.backend.common.data.entity.container_registry import ContainerRegistryEntityType
from ai.backend.common.exception import ErrorDetail
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityError, EntityErrorCode


class InvalidContainerRegistryProject(EntityError):
    """A Harbor project name the registry cannot be stored under.

    The same validation runs on the way in and on a later edit, and the two report
    different operations, so a caller names which one by picking a subclass.
    """


class InvalidContainerRegistryProjectOnCreate(InvalidContainerRegistryProject, web.HTTPBadRequest):
    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ContainerRegistryEntityType(), ActionOperationType.CREATE, ErrorDetail.BAD_REQUEST
        )


class InvalidContainerRegistryProjectOnModify(InvalidContainerRegistryProject, web.HTTPBadRequest):
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
