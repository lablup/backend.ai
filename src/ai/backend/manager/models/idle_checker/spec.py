from __future__ import annotations

from typing import Any

from ai.backend.manager.models.base import ABCColumnPayload


class IdleCheckerSpecABC(ABCColumnPayload):
    """
    Base for idle checker spec payloads stored in ``idle_checkers.spec``.

    Declares the :class:`ABCColumnPayload` serialize/load contract but leaves it
    unimplemented for now. The polymorphic serialization (dispatching by
    ``checker_type``) and the concrete per-``checker_type`` specs land in a
    follow-up; this PR only establishes the payload base type.
    """

    def serialize(self) -> dict[str, Any]:
        raise NotImplementedError

    @classmethod
    def load(cls, raw: dict[str, Any]) -> IdleCheckerSpecABC:
        raise NotImplementedError
