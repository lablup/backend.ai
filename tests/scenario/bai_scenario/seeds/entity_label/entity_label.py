"""Write specs for a label put on an entity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.entity_label import EntityLabelKey
from ai.backend.common.data.entity.types import RuntimeEntityID
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.entity_label.types import EntityLabelData
from ai.backend.manager.models.entity_label.upserters import EntityLabelUpserter
from bai_scenario.seeds.seeder import TestSeedFieldUpserter


@dataclass(frozen=True)
class TestSeedDomainLabel(TestSeedFieldUpserter[DomainData, EntityLabelData]):
    """One `key=value` label on a domain."""

    key: str
    value: str

    @override
    def kind(self) -> str:
        return f"라벨 {self.key}={self.value}"

    @override
    def owner_id(self, owner: DomainData) -> RuntimeEntityID:
        return RuntimeEntityID(DomainEntityType(), owner.id)

    @override
    def seed(self) -> EntityLabelUpserter:
        return EntityLabelUpserter(key=EntityLabelKey(self.key), value=self.value)
