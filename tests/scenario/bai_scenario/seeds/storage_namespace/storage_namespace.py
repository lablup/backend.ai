"""Write specs for a storage namespace."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.data.storage_namespace.types import StorageNamespaceData
from ai.backend.manager.models.storage_namespace.creators import StorageNamespaceCreator
from ai.backend.testutils.scenario_steps import Says
from bai_scenario.seeds.seeder import Naming, TestSeedRowFrom

SEEDED_NAMESPACE = "seeded-bucket"
"""The name a namespace is registered under unless the spec says otherwise."""


@dataclass(frozen=True)
class TestSeedStorageNamespace(TestSeedRowFrom[ObjectStorageData, StorageNamespaceData]):
    """A namespace registered under one object storage."""

    namespace: str = SEEDED_NAMESPACE

    @override
    def kind(self) -> str:
        return Says("저장소 네임스페이스", english="storage namespace")

    @override
    def detail(self) -> str:
        return Says(
            "오브젝트 스토리지에 등록된 버킷 이름입니다",
            english="a bucket name registered on the object storage",
        )

    @override
    def name(self, naming: Naming) -> str:
        return self.namespace

    @override
    def seed(self, name: str, storage: ObjectStorageData) -> StorageNamespaceCreator:
        return StorageNamespaceCreator(storage_id=storage.id, namespace=self.namespace)
