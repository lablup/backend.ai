from __future__ import annotations

from ai.backend.manager.errors.common import GenericBadRequest, GenericForbidden, ObjectNotFound

__all__ = (
    "AppConfigAllowListNotFound",
    "AppConfigDefinitionNotFound",
    "AppConfigFragmentNotFound",
    "AppConfigFragmentWriteNotAllowed",
    "AppConfigFragmentForbidden",
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


class AppConfigFragmentWriteNotAllowed(GenericBadRequest):
    """A fragment write was rejected by the write-gate.

    Raised when the target ``config_name`` is not registered, or no app_config_allow_list
    row exists for the target ``(config_name, scope_type)`` pair.
    """

    error_type = "https://api.backend.ai/probs/app-config-fragment-write-not-allowed"
    error_title = "App config fragment write is not allowed for this config/scope."


class AppConfigFragmentForbidden(GenericForbidden):
    """A self-service write targeted a fragment the caller does not own.

    Raised when a ``my`` write path targets a fragment that is not the caller's own
    user-scope row.
    """

    error_type = "https://api.backend.ai/probs/app-config-fragment-forbidden"
    error_title = "You are not allowed to modify this app config fragment."
