from __future__ import annotations

from ai.backend.manager.errors.common import GenericBadRequest, ObjectNotFound

__all__ = (
    "IdleCheckerNotFound",
    "IdleCheckerOwnerScopeNotSupported",
    "IdleCheckerTypeChangeNotAllowed",
)


class IdleCheckerNotFound(ObjectNotFound):
    error_type = "https://api.backend.ai/probs/idle-checker-not-found"
    object_name = "idle checker"


class IdleCheckerOwnerScopeNotSupported(GenericBadRequest):
    error_type = "https://api.backend.ai/probs/idle-checker-owner-scope-not-supported"
    error_title = "The idle checker owner scope is not supported."


class IdleCheckerTypeChangeNotAllowed(GenericBadRequest):
    error_type = "https://api.backend.ai/probs/idle-checker-type-change-not-allowed"
    error_title = "Changing an idle checker's type is not allowed."
