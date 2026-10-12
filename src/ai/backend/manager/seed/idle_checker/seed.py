from __future__ import annotations

from collections.abc import Sequence
from typing import override

from pydantic import Field

from ai.backend.common.data.entity.idle_checker import IdleCheckerID
from ai.backend.common.data.idle_checker.types import IdleCheckerSpec
from ai.backend.common.types import SessionTypes
from ai.backend.manager.models.idle_checker.upserters import IdleCheckerUpserter
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite
from ai.backend.manager.seed.base import SeedItem, SeedItems, SeedRejection


class IdleCheckerSeed(SeedItem):
    """One ``idle_checkers`` row, keyed by its stated id."""

    id: IdleCheckerID
    name: str = Field(min_length=1, max_length=128)
    description: str | None = None
    target_session_types: list[SessionTypes] = Field(min_length=1)
    initial_grace_period_seconds: int = Field(default=0, ge=0)
    spec: IdleCheckerSpec

    @override
    def key(self) -> str:
        return str(self.id)

    @override
    def write(self) -> SeedWrite:
        return SeedWrite(
            upserter=IdleCheckerUpserter(
                id=self.id,
                name=self.name,
                description=self.description,
                target_session_types=self.target_session_types,
                initial_grace_period_seconds=self.initial_grace_period_seconds,
                spec=self.spec,
            ),
            field_upserters=[],
            field_purgers=[],
        )

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[IdleCheckerSeed]]) -> list[SeedRejection]:
        return []
