from __future__ import annotations

from ai.backend.common.data.entity.app_config_definition import AppConfigDefinitionEntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.common import GenericForbidden

__all__ = (
    "AppConfigDefinitionNotFound",
    "AppConfigFragmentWriteNotAllowed",
)


class AppConfigDefinitionNotFound(EntityNotFoundError):
    error_type = "https://api.backend.ai/probs/app-config-definition-not-found"
    error_title = "The app config definition does not exist."

    def __init__(
        self,
        extra_msg: str | None = None,
        *,
        operation: ActionOperationType = ActionOperationType.GET,
    ) -> None:
        super().__init__(
            extra_msg, entity_type=AppConfigDefinitionEntityType(), operation=operation
        )


class AppConfigFragmentWriteNotAllowed(GenericForbidden):
    """A fragment write was rejected by the write-gate.

    Raised when the target ``config_name`` is not registered, or no app_config_allow_list
    row exists for the target ``(config_name, scope_type)`` pair.
    """

    error_type = "https://api.backend.ai/probs/app-config-fragment-write-not-allowed"
    error_title = "App config fragment write is not allowed for this config/scope."
