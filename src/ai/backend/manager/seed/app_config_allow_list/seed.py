from __future__ import annotations

from collections.abc import Sequence
from typing import override

from pydantic import Field

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.manager.models.app_config_allow_list.upserters import (
    AppConfigAllowListUpserter,
)
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite
from ai.backend.manager.seed.base import SeedItem, SeedItems, SeedRejection


class AppConfigAllowListSeed(SeedItem):
    """One ``app_config_allow_list`` row, keyed by its config name and scope type.
    ``rank`` left out takes the scope type's default."""

    config_name: str = Field(min_length=1, max_length=128)
    scope_type: AppConfigScopeType
    rank: int | None = Field(default=None, ge=-(2**31), le=2**31 - 1)

    @override
    def key(self) -> str:
        return f"{self.config_name}:{self.scope_type.value}"

    @override
    def write(self) -> SeedWrite:
        return SeedWrite(
            upserter=AppConfigAllowListUpserter(
                config_name=self.config_name, scope_type=self.scope_type, rank=self.rank
            ),
            field_upserters=[],
            field_purgers=[],
        )

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[AppConfigAllowListSeed]]) -> list[SeedRejection]:
        return []
