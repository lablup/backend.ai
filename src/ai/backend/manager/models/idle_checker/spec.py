from __future__ import annotations

from collections.abc import Sequence
from typing import Any, override

from ai.backend.manager.models.base import ABCColumnPayload


# Placeholder contract types — fleshed out by the checker-logic stories.
# Per-tick context (DB/Valkey/Prometheus handles) prepare() reads runtime state through.
class IdleCheckContext: ...


# One session under idle evaluation, carrying the facts a checker judges against.
class IdleCheckTarget: ...


# Runtime state prepare() batch-reads for its targets, consumed by the judgment step.
class PreparedCheckerState: ...


class IdleCheckerSpecABC(ABCColumnPayload):
    """Config payload stored in ``idle_checkers.spec``. The ``serialize`` / ``load``
    discriminated dispatch and the ``prepare`` runtime-read contract land in follow-up
    stories."""

    @override
    def serialize(self) -> dict[str, Any]:
        raise NotImplementedError

    @classmethod
    @override
    def load(cls, raw: dict[str, Any]) -> IdleCheckerSpecABC:
        raise NotImplementedError

    def prepare(
        self, context: IdleCheckContext, targets: Sequence[IdleCheckTarget]
    ) -> PreparedCheckerState:
        raise NotImplementedError
