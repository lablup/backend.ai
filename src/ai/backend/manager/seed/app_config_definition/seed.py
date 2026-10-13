from __future__ import annotations

from collections.abc import Sequence
from typing import override

from pydantic import Field

from ai.backend.manager.models.app_config_definition.upserters import (
    AppConfigDefinitionUpserter,
)
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite
from ai.backend.manager.seed.base import SeedItem, SeedItems, SeedRejection


class AppConfigDefinitionSeed(SeedItem):
    """One ``app_config_definitions`` row, keyed by its config name."""

    config_name: str = Field(min_length=1, max_length=128)

    @override
    def key(self) -> str:
        return self.config_name

    @override
    def write(self) -> SeedWrite:
        return SeedWrite(
            upserter=AppConfigDefinitionUpserter(config_name=self.config_name),
            field_upserters=[],
            field_purgers=[],
        )

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[AppConfigDefinitionSeed]]) -> list[SeedRejection]:
        return []
