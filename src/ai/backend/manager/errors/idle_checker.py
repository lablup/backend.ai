from __future__ import annotations

from ai.backend.manager.errors.common import GenericBadRequest, ObjectNotFound

__all__ = (
    "IdleCheckerNotFound",
    "IdleCheckerTypeChangeNotAllowed",
)


class IdleCheckerNotFound(ObjectNotFound):
    error_type = "https://api.backend.ai/probs/idle-checker-not-found"
    object_name = "idle checker"


class IdleCheckerTypeChangeNotAllowed(GenericBadRequest):
    error_type = "https://api.backend.ai/probs/idle-checker-type-change-not-allowed"
    error_title = "Changing an idle checker's type is not allowed."
