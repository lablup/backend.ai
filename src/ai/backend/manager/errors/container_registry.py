from typing import override

from aiohttp import web

from ai.backend.common.data.entity.container_registry import ContainerRegistryEntityType
from ai.backend.common.exception import ErrorDetail
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityError, EntityErrorCode


class ContainerRegistryQuotaNotSupported(EntityError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/container-registry/quota-not-supported"
    error_title = "The container registry type does not support quota management."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ContainerRegistryEntityType(),
            ActionOperationType.GET,
            ErrorDetail.NOT_IMPLEMENTED,
        )


class ContainerRegistryQuotaNotConfigurable(EntityError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/container-registry/quota-not-configurable"
    error_title = "The container registry lacks the project or credentials for quota management."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ContainerRegistryEntityType(),
            ActionOperationType.GET,
            ErrorDetail.INVALID_PARAMETERS,
        )


class ContainerRegistryQuotaAlreadyExists(EntityError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/container-registry/quota-already-exists"
    error_title = "The container registry project already has a quota."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ContainerRegistryEntityType(),
            ActionOperationType.CREATE,
            ErrorDetail.ALREADY_EXISTS,
        )
