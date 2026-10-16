"""Write specs for an object storage registration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.models.object_storage.creators import ObjectStorageCreator
from bai_scenario.seeds.seeder import Naming, TestSeedRow

SEEDED_HOST = "seeded.object-storage.test"


@dataclass(frozen=True)
class TestSeedObjectStorage(TestSeedRow[ObjectStorageData]):
    """An object storage registration, created in global alone."""

    name_hint: str = "object-storage"

    @override
    def kind(self) -> str:
        return "object storage"

    @override
    def detail(self) -> str:
        return f"호스트가 {SEEDED_HOST} 이다"

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str) -> ObjectStorageCreator:
        return ObjectStorageCreator(
            name=name,
            host=SEEDED_HOST,
            access_key="seeded-access-key",
            secret_key="seeded-secret-key",
            endpoint="http://seeded.object-storage.test",
            region="seeded-region",
        )
