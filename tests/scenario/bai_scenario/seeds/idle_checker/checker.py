"""Write specs for an idle checker and its binding to a scope."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.idle_checker import IdleCheckerID
from ai.backend.common.data.idle_checker.types import (
    CheckerType,
    IdleCheckerSpec,
    SessionLifetimeSpec,
)
from ai.backend.common.types import SessionTypes
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.idle_checker.types import IdleCheckerData
from ai.backend.manager.models.idle_checker.creators import (
    IdleCheckerAssignmentCreator,
    IdleCheckerCreator,
)
from bai_scenario.seeds.seeder import Naming, TestSeedLink, TestSeedRow


@dataclass(frozen=True)
class TestSeedIdleChecker(TestSeedRow[IdleCheckerData]):
    """A checker in the global catalog that ends interactive sessions past a lifetime."""

    name_hint: str = "idle-checker"
    max_lifetime_seconds: int = 3600

    @override
    def kind(self) -> str:
        return "유휴 검사기"

    @override
    def detail(self) -> str:
        return f"대화형 세션을 {self.max_lifetime_seconds}초 뒤에 끝낸다"

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str) -> IdleCheckerCreator:
        return IdleCheckerCreator(
            name=name,
            description=None,
            target_session_types=[SessionTypes.INTERACTIVE],
            initial_grace_period_seconds=0,
            spec=IdleCheckerSpec(
                type=CheckerType.SESSION_LIFETIME,
                session_lifetime=SessionLifetimeSpec(
                    max_lifetime_seconds=self.max_lifetime_seconds
                ),
            ),
        )


@dataclass(frozen=True)
class AssignToDomain(TestSeedLink[DomainData, IdleCheckerData]):
    """The checker applies to every session of that domain."""

    @override
    def kind(self) -> str:
        return "에 켜 둔"

    @override
    def scope_id(self, scope: DomainData) -> DomainID:
        return scope.id

    @override
    def target_id(self, target: IdleCheckerData) -> IdleCheckerID:
        return target.id

    @override
    def seed(self) -> IdleCheckerAssignmentCreator:
        return IdleCheckerAssignmentCreator(enabled=True)
