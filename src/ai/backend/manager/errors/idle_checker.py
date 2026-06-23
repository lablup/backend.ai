from __future__ import annotations

from ai.backend.manager.errors.common import GenericBadRequest

__all__ = ("InvalidIdleCheckerSpec",)


class InvalidIdleCheckerSpec(GenericBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-idle-checker-spec"
    error_title = "The idle checker spec is malformed or its checker_type is unknown."
