from __future__ import annotations

from collections.abc import Sequence
from typing import override

from pydantic import Field

from ai.backend.common.data.entity.login_client_type import LoginClientTypeID
from ai.backend.manager.models.login_client_type.upserters import LoginClientTypeUpserter
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite
from ai.backend.manager.seed.base import SeedItem, SeedItems, SeedRejection


class LoginClientTypeSeed(SeedItem):
    """One ``login_client_types`` row, keyed by its id."""

    id: LoginClientTypeID
    name: str = Field(min_length=1, max_length=64)
    description: str | None = None

    @override
    def key(self) -> str:
        return str(self.id)

    @override
    def write(self) -> SeedWrite:
        return SeedWrite(
            upserter=LoginClientTypeUpserter(
                id=self.id, name=self.name, description=self.description
            ),
            field_upserters=[],
            field_purgers=[],
        )

    @override
    def check(self) -> list[str]:
        return []

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[LoginClientTypeSeed]]) -> list[SeedRejection]:
        return []
