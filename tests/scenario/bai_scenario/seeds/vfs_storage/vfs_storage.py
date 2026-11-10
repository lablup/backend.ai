"""Write specs for a VFS storage registration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.models.vfs_storage.creators import VFSStorageCreator
from ai.backend.testutils.scenario_steps import Says
from bai_scenario.seeds.seeder import Naming, TestSeedRow

SEEDED_BASE_PATH = "/seeded/vfs-storage"


@dataclass(frozen=True)
class TestSeedVFSStorage(TestSeedRow[VFSStorageData]):
    """A VFS storage registration, created in global alone."""

    name_hint: str = "vfs-storage"

    @override
    def kind(self) -> str:
        return Says("VFS storage", english="VFS storage")

    @override
    def detail(self) -> str:
        return Says(
            f"기본 경로가 {SEEDED_BASE_PATH}입니다",
            english=f"its base path is {SEEDED_BASE_PATH}",
        )

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str) -> VFSStorageCreator:
        return VFSStorageCreator(name=name, host="seeded-host", base_path=SEEDED_BASE_PATH)
