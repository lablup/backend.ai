"""역할 단건 조회."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.entity.role import RoleEntityType
from ai.backend.common.dto.manager.v2.rbac.response import RoleNode
from ai.backend.manager.api.adapters.rbac.adapter import RBACAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.domain import TheCallIsRefused
from bai_scenario.components.rbac import (
    Granted,
    RoleLook,
    RolesAndACaller,
    RolesAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type RoleStep = Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, RoleNode]


@dataclass(frozen=True)
class ReadingTheRole(When[RolesAndACaller, RBACAdapter, RoleNode]):
    """미리 만든 역할을 id 로 읽는다."""

    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.role.name} 의 id 로 역할을 읽습니다",
            english=f"{laid.caller.username} reads {laid.role.name} by id",
        )

    @override
    async def call(self, adapter: RBACAdapter, laid: RolesAndACaller) -> RoleNode:
        with ActingAs(laid.caller):
            return await adapter.get(laid.role.id)


@dataclass(frozen=True)
class TheRoleNode(Then[RolesAndACaller, RoleNode]):
    """미리 만든 역할 전체가 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 역할 전체가 응답으로 옵니다",
            english="the whole role seeded in advance comes back",
        )

    @override
    def look(self, laid: RolesAndACaller, answered: Answered[RoleNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return RoleLook(self.started).verdicts("", node, laid.role, laid.domain.id)


@dataclass(frozen=True)
class AUserGrantedReadReadsTheRole(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, RoleNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-read-reads-the-role"

    @override
    def describe(self) -> str:
        return Says(
            "대상 도메인에서 역할 조회 권한을 받은 사용자가 역할을 읽으면, 미리 저장한 역할 "
            "전체가 응답으로 옵니다",
            english=(
                "when a user granted role read permission in a domain reads a role, the whole "
                "role seeded in advance comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(grant=(Granted(RoleEntityType(), Permission.READ),))

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, RoleNode]:
        return ReadingTheRole()

    @override
    def then(self) -> Then[RolesAndACaller, RoleNode]:
        return TheRoleNode(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRead(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, RoleNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-a-role"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자는 역할을 읽을 수 없습니다",
            english="a user granted nothing cannot read a role",
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone()

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, RoleNode]:
        return ReadingTheRole()

    @override
    def then(self) -> Then[RolesAndACaller, RoleNode]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[RoleStep] = [
    AUserGrantedReadReadsTheRole(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotRead(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: RoleStep, adapter: RBACAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
