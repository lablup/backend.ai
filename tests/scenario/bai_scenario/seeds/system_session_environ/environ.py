"""Write specs for a system session environ row."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironID
from ai.backend.common.data.system_session_environ.types import SystemSessionEnvironValueSource
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.data.system_session_environ.types import SystemSessionEnvironData
from ai.backend.manager.models.specs.soft_delete import SoftDeleteUpdater
from ai.backend.manager.models.system_session_environ.creators import (
    SystemSessionEnvironCreator,
)
from ai.backend.manager.models.system_session_environ.row import SystemSessionEnvironRow
from ai.backend.manager.models.system_session_environ.searchable_fields import (
    SystemSessionEnvironSearchableFields,
)
from ai.backend.testutils.scenario_steps import Says
from bai_scenario.seeds.seeder import Naming, TestSeedRow, TestSeedRowFrom

SEEDED_KEY = "SCENARIO_SEEDED_KEY"
"""The key a seeded row injects under."""


@dataclass(frozen=True)
class TestSeedSystemSessionEnviron(TestSeedRow[SystemSessionEnvironData]):
    """One binding at the public scope: the value source every session receives."""

    key: str = SEEDED_KEY
    value_source: SystemSessionEnvironValueSource = SystemSessionEnvironValueSource.SESSION_ID

    @override
    def kind(self) -> str:
        return Says("시스템 세션 환경변수", english="system session environ")

    @override
    def detail(self) -> str:
        return Says(
            f"public 범위에서 {self.value_source.value} 값을 주입합니다",
            english=f"injects the {self.value_source.value} value at the public scope",
        )

    @override
    def name(self, naming: Naming) -> str:
        return self.key

    @override
    def seed(self, name: str) -> SystemSessionEnvironCreator:
        return SystemSessionEnvironCreator(
            owner=global_entity_id(GlobalEntityName.PUBLIC),
            value_source=self.value_source,
            key=self.key,
        )


@dataclass(frozen=True)
class TestSeedDeletedSystemSessionEnviron(
    TestSeedRowFrom[SystemSessionEnvironData, SystemSessionEnvironData]
):
    """The row a previous seed laid, soft-deleted as the manager's delete writes it."""

    @override
    def kind(self) -> str:
        return Says("삭제된 시스템 세션 환경변수", english="deleted system session environ")

    @override
    def detail(self) -> str:
        return Says("지운 시각이 기록돼 있습니다", english="its deletion time is recorded")

    @override
    def name(self, naming: Naming) -> str:
        return naming("deleted-environ")

    @override
    def seed(
        self, name: str, source: SystemSessionEnvironData
    ) -> SoftDeleteUpdater[SystemSessionEnvironRow, SystemSessionEnvironData]:
        return SoftDeleteUpdater(
            target_row=SystemSessionEnvironRow,
            target_column=SystemSessionEnvironRow.id,
            target_id=SystemSessionEnvironID(source.id),
            converter=SystemSessionEnvironSearchableFields.own,
        )
