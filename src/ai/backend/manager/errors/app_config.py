from __future__ import annotations

from typing import override

from ai.backend.common.exception import ErrorCode, ErrorDetail, ErrorDomain, ErrorOperation
from ai.backend.manager.errors.common import (
    GenericBadRequest,
    GenericForbidden,
    ObjectNotFound,
)

__all__ = (
    "AppConfigAllowListNotFound",
    "AppConfigDefinitionNotFound",
    "AppConfigFragmentNotFound",
    "AppConfigFragmentTooLarge",
    "AppConfigFragmentWriteNotAllowed",
)


class AppConfigDefinitionNotFound(ObjectNotFound):
    error_type = "https://api.backend.ai/probs/app-config-definition-not-found"
    object_name = "app config definition"


class AppConfigAllowListNotFound(ObjectNotFound):
    error_type = "https://api.backend.ai/probs/app-config-allow-list-not-found"
    object_name = "app config allow-list entry"


class AppConfigFragmentNotFound(ObjectNotFound):
    error_type = "https://api.backend.ai/probs/app-config-fragment-not-found"
    object_name = "app config fragment"


class AppConfigFragmentWriteNotAllowed(GenericForbidden):
    """A fragment write was rejected by the write-gate.

    Raised when the target ``config_name`` is not registered, or no app_config_allow_list
    row exists for the target ``(config_name, scope_type)`` pair.
    """

    error_type = "https://api.backend.ai/probs/app-config-fragment-write-not-allowed"
    error_title = "App config fragment write is not allowed for this config/scope."


class AppConfigFragmentTooLarge(GenericBadRequest):
    """A fragment write was rejected for exceeding the per-fragment size limit.

    The size is checked before the batch reaches the repository, so one oversize item
    rejects the whole bulk upsert.
    """

    error_type = "https://api.backend.ai/probs/app-config-fragment-too-large"
    error_title = "App config fragment exceeds the maximum size."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.APP_CONFIG_FRAGMENT,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )
