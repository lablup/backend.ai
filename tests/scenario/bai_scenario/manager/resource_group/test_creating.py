"""리소스 그룹 생성 — 누가 만들 수 있고, 무엇이 이름과 기본 그룹을 막는가."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.resource_group.request import (
    CreateResourceGroupInput,
    CreateResourceGroupSchedulerOptionsConfigInput,
    CreateResourceGroupSchedulerOptionsInput,
)
from ai.backend.common.dto.manager.v2.resource_group.response import ResourceGroupDetailNode
from ai.backend.common.exception import ResourceGroupConflict
from ai.backend.common.types import AgentSelectionStrategy, SessionTypes
from ai.backend.manager.api.adapters.resource_group.adapter import ResourceGroupAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.resource import DefaultResourceGroupAlreadyExists
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.resource_group import (
    AGroupAndACaller,
    AGroupAndSomeone,
    TheNewGroupNode,
)
from bai_scenario.components.system import ACaller, SomeoneAlone
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type CreatingStep = Scenario[TestSeedingSession, Any, ResourceGroupAdapter, ResourceGroupDetailNode]


@dataclass(frozen=True)
class Creating(When[Any, ResourceGroupAdapter, ResourceGroupDetailNode]):
    """리소스 그룹을 만든다. 이름을 대지 않으면 미리 만들어 둔 그룹의 이름을 그대로 쓴다."""

    named: str | None = None
    is_default: bool = False

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: Any) -> str:
        if self.is_default:
            what_ko = "기본 그룹으로 "
            what_en = " as the default group"
        else:
            what_ko = ""
            what_en = ""
        return Says(
            f"{laid.caller.username}이 {self.named or laid.group.name}을 {what_ko}생성합니다",
            english=f"{laid.caller.username} creates {self.named or laid.group.name}{what_en}",
        )

    @override
    async def call(self, adapter: ResourceGroupAdapter, laid: Any) -> ResourceGroupDetailNode:
        with ActingAs(laid.caller):
            payload = await adapter.create(
                CreateResourceGroupInput(
                    name=self.named or laid.group.name,
                    domain_name=laid.caller.domain_name,
                    is_default=self.is_default,
                )
            )
        return payload.resource_group


@dataclass(frozen=True)
class CreatingWithSchedulerOptions(When[ACaller, ResourceGroupAdapter, ResourceGroupDetailNode]):
    """스케줄러 옵션을 지정해 그룹을 만든다."""

    named: str

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: ACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {self.named}을 허용 세션 타입, 대기 제한 시간, "
            "대기 세션 건너뛰기 재시도 횟수, 에이전트 선택 전략, 분할 자원 조각화 허용 여부, "
            "자동 정리할 라우트 상태를 지정해 생성합니다",
            english=(
                f"{laid.caller.username} creates {self.named} with the allowed session types, "
                "the pending timeout, the retries before skipping a pending session, the agent "
                "selection strategy, whether fractional resources may fragment and the route "
                "statuses to clean up"
            ),
        )

    @override
    async def call(self, adapter: ResourceGroupAdapter, laid: ACaller) -> ResourceGroupDetailNode:
        with ActingAs(laid.caller):
            payload = await adapter.create(
                CreateResourceGroupInput(
                    name=self.named,
                    domain_name=laid.caller.domain_name,
                    scheduler_options=CreateResourceGroupSchedulerOptionsInput(
                        allowed_session_types=[SessionTypes.BATCH],
                        pending_timeout=60,
                        config=CreateResourceGroupSchedulerOptionsConfigInput(
                            num_retries_to_skip=3
                        ),
                        agent_selection_strategy=AgentSelectionStrategy.CONCENTRATED,
                        allow_fractional_resource_fragmentation=False,
                        route_cleanup_target_statuses=["unhealthy", "degraded"],
                    ),
                )
            )
        return payload.resource_group


@dataclass(frozen=True)
class TheSuperadminMakesAGroup(
    Scenario[TestSeedingSession, ACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-makes-a-resource-group"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 이름만 주고 자원 그룹을 생성하면, 활성이고 공개이며 기본이 아닌 그룹 "
            "전체가 코드의 기본값으로 채워져 반환됩니다",
            english=(
                "when the superadmin creates a resource group with only a name, the whole group "
                "comes back active, public and not the default, filled from the defaults in "
                "the code"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return Creating(named="compute")

    @override
    def then(self) -> Then[ACaller, ResourceGroupDetailNode]:
        return TheNewGroupNode(started=self.started, named="compute")


@dataclass(frozen=True)
class TheSuperadminMakesAGroupWithItsSchedulerOptions(
    Scenario[TestSeedingSession, ACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-makes-a-resource-group-with-its-scheduler-options"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 스케줄러 옵션을 지정해 자원 그룹을 생성하면 지정한 옵션으로 채워진 "
            "그룹 전체가 반환됩니다",
            english=(
                "when the superadmin creates a resource group with its scheduler options, the "
                "whole group comes back with those options"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return CreatingWithSchedulerOptions(named="batch-only")

    @override
    def then(self) -> Then[ACaller, ResourceGroupDetailNode]:
        return TheNewGroupNode(
            started=self.started,
            named="batch-only",
            allowed_session_types=(SessionTypes.BATCH,),
            pending_timeout=60.0,
            num_retries_to_skip=3,
            agent_selection_strategy=AgentSelectionStrategy.CONCENTRATED,
            allow_fractional_resource_fragmentation=False,
            route_cleanup_target_statuses=("unhealthy", "degraded"),
        )


@dataclass(frozen=True)
class ADefaultGroupIsMade(
    Scenario[TestSeedingSession, ACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-resource-group-made-as-the-default-answers-default"

    @override
    def describe(self) -> str:
        return Says(
            "기본 그룹이 없을 때 superadmin 이 기본으로 지정해 생성하면 기본인 그룹이 반환됩니다",
            english=(
                "when no default group exists and the superadmin creates one designated as the "
                "default, the group comes back as the default"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return Creating(named="primary", is_default=True)

    @override
    def then(self) -> Then[ACaller, ResourceGroupDetailNode]:
        return TheNewGroupNode(started=self.started, named="primary", is_default=True)


@dataclass(frozen=True)
class ANameAnotherGroupHoldsIsRefused(
    Scenario[TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    @override
    def summary(self) -> str:
        return "a-name-another-resource-group-already-holds-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "이미 어떤 자원 그룹이 쓰고 있는 이름으로 생성하려 하면 이름 중복으로 거부됩니다",
            english=(
                "creating with a name another resource group already holds is rejected as a "
                "duplicate name"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return Creating()

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheCallIsRefused(ResourceGroupConflict)


@dataclass(frozen=True)
class ASecondDefaultIsRefused(
    Scenario[TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    @override
    def summary(self) -> str:
        return "a-second-default-resource-group-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "기본 그룹이 이미 있을 때 다른 이름으로 또 기본 그룹을 생성하려 하면 기본 그룹이 "
            "이미 있다는 이유로 거부됩니다",
            english=(
                "when a default group already exists, creating another default group under a "
                "different name is rejected because a default group already exists"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.SUPERADMIN, is_default=True)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return Creating(named="another-default", is_default=True)

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheCallIsRefused(DefaultResourceGroupAlreadyExists)


@dataclass(frozen=True)
class AUserWhoIsNotTheSuperadminMayNotCreate(
    Scenario[TestSeedingSession, ACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-make-a-resource-group"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 아닌 사용자가 자원 그룹을 생성하려 하면 역할 부족으로 거부됩니다",
            english=(
                "when a user who is not the superadmin tries to create a resource group, the "
                "call is rejected for lacking the role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACaller]:
        return SomeoneAlone()

    @override
    def when(self) -> When[ACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return Creating(named="by-a-user")

    @override
    def then(self) -> Then[ACaller, ResourceGroupDetailNode]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class TheMonitorMayNotCreate(
    Scenario[TestSeedingSession, ACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    @override
    def summary(self) -> str:
        return "the-monitor-may-not-make-a-resource-group"

    @override
    def describe(self) -> str:
        return Says(
            "모니터가 자원 그룹을 생성하려 하면 역할 부족으로 거부됩니다. 모니터는 읽기만 "
            "통과합니다",
            english=(
                "when the monitor tries to create a resource group, the call is rejected for "
                "lacking the role. the monitor passes reads only"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.MONITOR)

    @override
    def when(self) -> When[ACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return Creating(named="by-the-monitor")

    @override
    def then(self) -> Then[ACaller, ResourceGroupDetailNode]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[CreatingStep] = [
    TheSuperadminMakesAGroup(started=datetime.now(UTC)),
    TheSuperadminMakesAGroupWithItsSchedulerOptions(started=datetime.now(UTC)),
    ADefaultGroupIsMade(started=datetime.now(UTC)),
    ANameAnotherGroupHoldsIsRefused(),
    # TODO(BA-7946): the create path maps every unique violation to a name conflict, so a
    # second default is refused as ResourceGroupConflict; list this row once it raises
    # DefaultResourceGroupAlreadyExists like the update path.
    # ASecondDefaultIsRefused(),
    AUserWhoIsNotTheSuperadminMayNotCreate(),
    TheMonitorMayNotCreate(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: CreatingStep, adapter: ResourceGroupAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
