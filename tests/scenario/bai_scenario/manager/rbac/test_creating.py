"""역할 생성."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.role import RoleEntityType
from ai.backend.common.dto.manager.v2.rbac.request import CreateRoleInput
from ai.backend.common.dto.manager.v2.rbac.response import CreateRolePayload
from ai.backend.common.dto.manager.v2.rbac.types import (
    RoleSourceDTO,
    RoleStatusDTO,
    ScopeInputDTO,
)
from ai.backend.manager.api.adapters.rbac.adapter import RBACAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Says,
    Scenario,
    Skipped,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.domain import TheCallIsRefused, WrittenByThisRun
from bai_scenario.components.rbac import (
    DOMAIN_OF_ROLE,
    Granted,
    RolesAndACaller,
    RolesAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

CREATED_NAME = "made-role"
CREATED_DESCRIPTION = Says("새로 만든 역할", english="a role made by this call")

type Created = CreateRolePayload
type RoleStep = Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, Created]


@dataclass(frozen=True)
class Creating(When[RolesAndACaller, RBACAdapter, Created]):
    """대상 도메인에 역할을 만든다."""

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 도메인 {laid.domain.name} 에 {CREATED_NAME} 역할을 만듭니다",
            english=(
                f"{laid.caller.username} creates the role {CREATED_NAME} in domain "
                f"{laid.domain.name}"
            ),
        )

    @override
    async def call(self, adapter: RBACAdapter, laid: RolesAndACaller) -> Created:
        with ActingAs(laid.caller):
            return await adapter.create(
                CreateRoleInput(
                    name=CREATED_NAME,
                    description=CREATED_DESCRIPTION,
                    scope=ScopeInputDTO(
                        scope_type=DomainEntityType(), scope_id=str(laid.domain.id)
                    ),
                )
            )


@dataclass(frozen=True)
class TheCreatedRole(Then[RolesAndACaller, Created]):
    """방금 만든 역할 전체가 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "만든 역할 전체가 응답으로 옵니다",
            english="the whole role just created comes back",
        )

    @override
    def look(self, laid: RolesAndACaller, answered: Answered[Created]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        node = payload.role
        written = WrittenByThisRun(self.started)
        return [
            Same("name", node.name, CREATED_NAME),
            Same("description", node.description, CREATED_DESCRIPTION),
            Same("source", node.source, RoleSourceDTO.CUSTOM),
            Same("status", node.status, RoleStatusDTO.ACTIVE),
            Same("auto_assign", node.auto_assign, False),
            Same("scope_type", node.scope_type, DomainEntityType()),
            Held[UUID]("scope_id", node.scope_id, SameAs(laid.domain.id, DOMAIN_OF_ROLE)),
            Same("role_preset_id", node.role_preset_id, None),
            Skipped("id", Says("데이터베이스가 생성합니다", english="the database generates it")),
            Held[UUID](
                "entity_id",
                node.entity_id,
                SameAs(
                    node.id,
                    Says("응답이 실은 id", english="the id the response carries"),
                ),
            ),
            Held("created_at", node.created_at, written),
            Held("updated_at", node.updated_at, written),
            Same("deleted_at", node.deleted_at, None),
        ]


@dataclass(frozen=True)
class AUserGrantedCreateMakesARole(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, Created]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-create-makes-a-role"

    @override
    def describe(self) -> str:
        return Says(
            "대상 도메인에서 역할 생성 권한을 받은 사용자가 역할을 만들면, 만든 역할 전체가 "
            "응답으로 옵니다",
            english=(
                "when a user granted role create permission in a domain creates a role, the "
                "whole role just created comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(grant=(Granted(RoleEntityType(), Permission.CREATE),))

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, Created]:
        return Creating()

    @override
    def then(self) -> Then[RolesAndACaller, Created]:
        return TheCreatedRole(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotCreate(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, Created]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-create-a-role"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자는 역할을 만들 수 없습니다",
            english="a user granted nothing cannot create a role",
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone()

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, Created]:
        return Creating()

    @override
    def then(self) -> Then[RolesAndACaller, Created]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[RoleStep] = [
    AUserGrantedCreateMakesARole(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotCreate(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: RoleStep, adapter: RBACAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
