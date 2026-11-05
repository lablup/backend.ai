"""유휴 검사기 할당 생성 — 검사기를 도메인에 켠다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.idle_checker_assignment.request import (
    CreateIdleCheckerAssignmentInput,
    IdleCheckerScopeRefDTO,
)
from ai.backend.common.dto.manager.v2.idle_checker_assignment.response import (
    IdleCheckerAssignmentNode,
)
from ai.backend.common.dto.manager.v2.idle_checker_assignment.types import IdleCheckerScopeTypeDTO
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.api.adapters.idle_checker_assignment.adapter import (
    IdleCheckerAssignmentAdapter,
)
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
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.domain import WrittenByThisRun
from bai_scenario.components.idle_checker import ACheckerAndADomain, ACheckerAndADomainAndACaller
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type CreatingStep = Scenario[
    TestSeedingSession,
    ACheckerAndADomainAndACaller,
    IdleCheckerAssignmentAdapter,
    IdleCheckerAssignmentNode,
]


@dataclass(frozen=True)
class EnablingTheCheckerOnTheDomain(
    When[ACheckerAndADomainAndACaller, IdleCheckerAssignmentAdapter, IdleCheckerAssignmentNode]
):
    """미리 저장한 검사기를 미리 저장한 도메인에 켠다."""

    @override
    def operation(self) -> str:
        return "admin_create"

    @override
    def describe(self, laid: ACheckerAndADomainAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 검사기를 도메인 {laid.domain.name}에 켭니다",
            english=(
                f"{laid.caller.username} enables the checker on the domain {laid.domain.name}"
            ),
        )

    @override
    async def call(
        self, adapter: IdleCheckerAssignmentAdapter, laid: ACheckerAndADomainAndACaller
    ) -> IdleCheckerAssignmentNode:
        request = CreateIdleCheckerAssignmentInput(
            scope=IdleCheckerScopeRefDTO(
                scope_type=IdleCheckerScopeTypeDTO.DOMAIN, scope_id=laid.domain.id
            ),
            idle_checker_id=laid.checker.id,
            enabled=True,
        )
        with ActingAs(laid.caller):
            payload = await adapter.admin_create(request)
        return payload.idle_checker_assignment


@dataclass(frozen=True)
class TheCreatedAssignmentNode(Then[ACheckerAndADomainAndACaller, IdleCheckerAssignmentNode]):
    """요청에서 지정한 검사기와 도메인을 잇는 할당이 활성 상태로 반환된다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "요청에서 지정한 검사기와 도메인을 잇는 할당이 활성 상태로 반환됩니다",
            english=(
                "the assignment between the checker and the domain the request named comes back "
                "enabled"
            ),
        )

    @override
    def look(
        self, laid: ACheckerAndADomainAndACaller, answered: Answered[IdleCheckerAssignmentNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(UnreachableError, answered.raised)]
        written = WrittenByThisRun(self.started)
        return [
            Skipped("id", Says("데이터베이스가 생성합니다", english="the database generates it")),
            Same("scope_type", node.scope_type, IdleCheckerScopeTypeDTO.DOMAIN),
            Held(
                "scope_id",
                node.scope_id,
                SameAs(
                    laid.domain.id,
                    Says("미리 저장한 도메인", english="the domain seeded in advance"),
                ),
            ),
            Held(
                "idle_checker_id",
                node.idle_checker_id,
                SameAs(
                    laid.checker.id,
                    Says("미리 저장한 검사기", english="the checker seeded in advance"),
                ),
            ),
            Same("enabled", node.enabled, True),
            Held("created_at", node.created_at, written),
            Held("updated_at", node.updated_at, written),
        ]


@dataclass(frozen=True)
class TheSuperadminEnablesTheCheckerOnTheDomain(
    Scenario[
        TestSeedingSession,
        ACheckerAndADomainAndACaller,
        IdleCheckerAssignmentAdapter,
        IdleCheckerAssignmentNode,
    ]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-enables-an-idle-checker-on-a-domain"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 검사기를 도메인에 켜면, 요청에서 지정한 검사기와 도메인을 잇는 "
            "할당이 활성 상태로 반환됩니다",
            english=(
                "when the superadmin enables a checker on a domain, the assignment between the "
                "checker and the domain the request named comes back enabled"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACheckerAndADomainAndACaller]:
        return ACheckerAndADomain(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[
        ACheckerAndADomainAndACaller, IdleCheckerAssignmentAdapter, IdleCheckerAssignmentNode
    ]:
        return EnablingTheCheckerOnTheDomain()

    @override
    def then(self) -> Then[ACheckerAndADomainAndACaller, IdleCheckerAssignmentNode]:
        return TheCreatedAssignmentNode(started=self.started)


@dataclass(frozen=True)
class AnAssignmentCreatedWithoutAUserIsRefused(
    Scenario[
        TestSeedingSession,
        ACheckerAndADomainAndACaller,
        IdleCheckerAssignmentAdapter,
        IdleCheckerAssignmentNode,
    ]
):
    @override
    def summary(self) -> str:
        return "an-assignment-created-without-a-user-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "검사기와 도메인이 있고 사용자 컨텍스트 없이 검사기를 도메인에 켜려 하면, "
            "호출자를 알 수 없어 거부됩니다",
            english=(
                "when a checker and a domain exist and the checker is enabled on the domain "
                "without a user context, it is rejected because the caller cannot be known"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACheckerAndADomainAndACaller]:
        return ACheckerAndADomain()

    @override
    def when(
        self,
    ) -> When[
        ACheckerAndADomainAndACaller, IdleCheckerAssignmentAdapter, IdleCheckerAssignmentNode
    ]:
        return EnablingTheCheckerOnTheDomain()

    @override
    def then(self) -> Then[ACheckerAndADomainAndACaller, IdleCheckerAssignmentNode]:
        return TheCallIsRefused(UnreachableError)


SCENARIOS: list[CreatingStep] = [
    TheSuperadminEnablesTheCheckerOnTheDomain(started=datetime.now(UTC)),
    AnAssignmentCreatedWithoutAUserIsRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: CreatingStep,
    adapter: IdleCheckerAssignmentAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
