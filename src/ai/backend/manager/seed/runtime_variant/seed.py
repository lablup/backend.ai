from __future__ import annotations

from collections.abc import Sequence
from typing import override

from pydantic import Field

from ai.backend.common.config import DefaultModelDefinition
from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.manager.models.runtime_variant.upserters import RuntimeVariantUpserter
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite
from ai.backend.manager.seed.base import SeedItem, SeedItems, SeedRejection


class RuntimeVariantSeed(SeedItem):
    """One ``runtime_variants`` row under its stated id."""

    id: RuntimeVariantID
    name: str = Field(min_length=1, max_length=128)
    description: str | None = None
    reads_vfolder_config_files: bool = False
    default_model_definition: DefaultModelDefinition = Field(default_factory=DefaultModelDefinition)

    @override
    def key(self) -> str:
        return str(self.id)

    @override
    def write(self) -> SeedWrite:
        return SeedWrite(
            upserter=RuntimeVariantUpserter(
                id=self.id,
                name=self.name,
                description=self.description,
                reads_vfolder_config_files=self.reads_vfolder_config_files,
                default_model_definition=self.default_model_definition,
            ),
            field_upserters=[],
            field_purgers=[],
        )

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[RuntimeVariantSeed]]) -> list[SeedRejection]:
        return []
