from __future__ import annotations

from typing import override

from ai.backend.common.data.entity.app_config_definition import AppConfigDefinitionEntityType
from ai.backend.common.exception import ErrorDetail
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityError, EntityErrorCode
from ai.backend.manager.errors.common import GenericForbidden, ObjectNotFound

__all__ = (
    "AppConfigDefinitionNotFound",
    "AppConfigFragmentWriteNotAllowed",
)


class AppConfigDefinitionNotFound(EntityError, ObjectNotFound):
    error_type = "https://api.backend.ai/probs/app-config-definition-not-found"
    object_name = "app config definition"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            AppConfigDefinitionEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )


class AppConfigFragmentWriteNotAllowed(GenericForbidden):
    """A fragment write was rejected by the write-gate.

    Raised when the target ``config_name`` is not registered, or no app_config_allow_list
    row exists for the target ``(config_name, scope_type)`` pair.
    """

    error_type = "https://api.backend.ai/probs/app-config-fragment-write-not-allowed"
    error_title = "App config fragment write is not allowed for this config/scope."
