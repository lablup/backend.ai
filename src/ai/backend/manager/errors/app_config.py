from __future__ import annotations

from ai.backend.manager.errors.common import GenericForbidden, ObjectNotFound

__all__ = (
    "AppConfigAllowListNotFound",
    "AppConfigDefinitionNotFound",
    "AppConfigFragmentNotFound",
    "AppConfigFragmentWriteNotAllowed",
    "AppConfigResolveNotAllowed",
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


class AppConfigResolveNotAllowed(GenericForbidden):
    """A merged-AppConfig read was requested for a principal other than the caller.

    Temporary per-request guard standing in for an RBAC validator: a resolve / scoped
    search whose ``user_id`` does not match the authenticated caller is rejected.
    """

    error_type = "https://api.backend.ai/probs/app-config-resolve-not-allowed"
    error_title = "App config resolve is not allowed for this principal."
