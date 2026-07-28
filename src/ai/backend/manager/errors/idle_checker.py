from __future__ import annotations

from ai.backend.manager.errors.common import ObjectNotFound

__all__ = ("IdleCheckerNotFound",)


class IdleCheckerNotFound(ObjectNotFound):
    error_type = "https://api.backend.ai/probs/idle-checker-not-found"
    object_name = "idle checker"
