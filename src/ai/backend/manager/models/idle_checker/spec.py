from __future__ import annotations

from typing import Any, override

from ai.backend.manager.models.base import ABCColumnPayload


class IdleCheckerSpecABC(ABCColumnPayload):
    """Config payload stored in ``idle_checkers.spec``. Concrete per-``checker_type`` specs
    and the serialize/load discriminated dispatch land in follow-up stories.

    Behavior (``prepare`` / ``check_idle``) lives on the sokovan ``IdleCheckerABC`` checker
    built from this config — not on the stored payload.
    """

    @override
    def serialize(self) -> dict[str, Any]:
        raise NotImplementedError

    @classmethod
    @override
    def load(cls, raw: dict[str, Any]) -> IdleCheckerSpecABC:
        raise NotImplementedError
