from typing import override

from aiohttp import web

from ai.backend.common.data.entity.container_registry import ContainerRegistryEntityType
from ai.backend.common.exception import ErrorDetail
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityError, EntityErrorCode


class InvalidContainerRegistryProject(EntityError, web.HTTPBadRequest):
    _operation: ActionOperationType

    def __init__(self, extra_msg: str | None = None, *, operation: ActionOperationType) -> None:
        self._operation = operation
        super().__init__(extra_msg)

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ContainerRegistryEntityType(), self._operation, ErrorDetail.BAD_REQUEST
        )


class InvalidContainerRegistryURL(EntityError, web.HTTPBadRequest):
    _operation: ActionOperationType

    def __init__(self, extra_msg: str | None = None, *, operation: ActionOperationType) -> None:
        self._operation = operation
        super().__init__(extra_msg)

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ContainerRegistryEntityType(), self._operation, ErrorDetail.BAD_REQUEST
        )
