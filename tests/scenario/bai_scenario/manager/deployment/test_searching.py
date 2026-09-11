"""배포 훑기 — 세 문이 서로 다른 것으로 막는다.

전역 훑기는 역할이 지킨다. 프로젝트 훑기는 그 프로젝트에, 내 것 훑기는 부르는 사람 자신의
스코프에 걸린 읽기 권한이 지킨다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.deployment import (
    DeploymentsInTwoProjects,
    ManyDeploymentsAndACaller,
    ManyDeploymentsInThatPlace,
    MineBesideAnothers,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.deployment.request import AdminSearchDeploymentsInput
from ai.backend.common.dto.manager.v2.deployment.response import AdminSearchDeploymentsPayload
from ai.backend.manager.api.adapters.deployment.adapter import DeploymentAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Same,
    Scenario,
    Then,
    Verdict,
    When,
)

type Searched = AdminSearchDeploymentsPayload
type SearchingStep = Scenario[
    SeedingSession, ManyDeploymentsAndACaller, DeploymentAdapter, Searched
]


@dataclass(frozen=True)
class SearchingEverything(When[ManyDeploymentsAndACaller, DeploymentAdapter, Searched]):
    """필터 없이 전체를 훑는다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyDeploymentsAndACaller) -> str:
        return f"{laid.caller.username}이 필터 없이 전체 조회"

    @override
    async def call(self, adapter: DeploymentAdapter, laid: ManyDeploymentsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(AdminSearchDeploymentsInput())


@dataclass(frozen=True)
class SearchingTheProject(When[ManyDeploymentsAndACaller, DeploymentAdapter, Searched]):
    """부르는 사람이 속한 프로젝트 안을 훑는다."""

    @override
    def operation(self) -> str:
        return "project_search"

    @override
    def describe(self, laid: ManyDeploymentsAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.place.project.name} 안을 조회"

    @override
    async def call(self, adapter: DeploymentAdapter, laid: ManyDeploymentsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.project_search(
                laid.place.project.id, AdminSearchDeploymentsInput()
            )


@dataclass(frozen=True)
class SearchingMine(When[ManyDeploymentsAndACaller, DeploymentAdapter, Searched]):
    """부르는 사람이 만든 것을 훑는다."""

    @override
    def operation(self) -> str:
        return "my_search"

    @override
    def describe(self, laid: ManyDeploymentsAndACaller) -> str:
        return f"{laid.caller.username}이 자기 것을 조회"

    @override
    async def call(self, adapter: DeploymentAdapter, laid: ManyDeploymentsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.my_search(AdminSearchDeploymentsInput())


@dataclass(frozen=True)
class EveryLaidDeploymentIsFound(Then[ManyDeploymentsAndACaller, Searched]):
    """답으로 받은 배포가 모두, 그리고 그것만 세어진다."""

    @override
    def says(self) -> str:
        return "심은 배포가 모두, 그리고 그것만 세어진다"

    @override
    def look(self, laid: ManyDeploymentsAndACaller, answered: Answered[Searched]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Same(
                "items",
                sorted(one.metadata.name for one in payload.items),
                sorted(one.metadata.name for one in laid.laid),
            ),
            Same("total_count", payload.total_count, len(laid.laid)),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheSuperadminCountsEveryOne(
    Scenario[SeedingSession, ManyDeploymentsAndACaller, DeploymentAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-counts-every-deployment"

    @override
    def describe(self) -> str:
        return "배포 셋이 있고 슈퍼관리자가 필터 없이 전체를 훑으면, 셋을 모두 센다"

    @override
    def given(self) -> Given[SeedingSession, ManyDeploymentsAndACaller]:
        return ManyDeploymentsInThatPlace(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyDeploymentsAndACaller, DeploymentAdapter, Searched]:
        return SearchingEverything()

    @override
    def then(self) -> Then[ManyDeploymentsAndACaller, Searched]:
        return EveryLaidDeploymentIsFound()


@dataclass(frozen=True)
class AGrantDoesNotOpenTheGlobalDoor(
    Scenario[SeedingSession, ManyDeploymentsAndACaller, DeploymentAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-may-not-search-every-deployment"

    @override
    def describe(self) -> str:
        return (
            "배포 읽기 권한을 받았지만 슈퍼관리자가 아닌 사용자가 전체를 훑으면, 역할로 "
            "거부된다. 이 문은 권한 그래프가 아니라 역할이 지킨다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyDeploymentsAndACaller]:
        return ManyDeploymentsInThatPlace(granted=(Permission.READ,))

    @override
    def when(self) -> When[ManyDeploymentsAndACaller, DeploymentAdapter, Searched]:
        return SearchingEverything()

    @override
    def then(self) -> Then[ManyDeploymentsAndACaller, Searched]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class OnlyThatProjectsOnesAreFound(
    Scenario[SeedingSession, ManyDeploymentsAndACaller, DeploymentAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "searching-a-project-finds-only-its-own-deployments"

    @override
    def describe(self) -> str:
        return (
            "두 프로젝트에 배포가 나뉘어 있고 한쪽에만 읽기 권한을 받은 사용자가 그 "
            "프로젝트를 훑으면, 그 프로젝트의 것만 나온다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyDeploymentsAndACaller]:
        return DeploymentsInTwoProjects(granted=(Permission.READ,))

    @override
    def when(self) -> When[ManyDeploymentsAndACaller, DeploymentAdapter, Searched]:
        return SearchingTheProject()

    @override
    def then(self) -> Then[ManyDeploymentsAndACaller, Searched]:
        return EveryLaidDeploymentIsFound()


@dataclass(frozen=True)
class AProjectWithNoGrantIsRefused(
    Scenario[SeedingSession, ManyDeploymentsAndACaller, DeploymentAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-a-project"

    @override
    def describe(self) -> str:
        return "그 프로젝트에 읽기 권한이 없는 사용자가 프로젝트를 훑으면, 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ManyDeploymentsAndACaller]:
        return ManyDeploymentsInThatPlace()

    @override
    def when(self) -> When[ManyDeploymentsAndACaller, DeploymentAdapter, Searched]:
        return SearchingTheProject()

    @override
    def then(self) -> Then[ManyDeploymentsAndACaller, Searched]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class OnlyMyOwnAreFound(
    Scenario[SeedingSession, ManyDeploymentsAndACaller, DeploymentAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "searching-my-own-finds-only-what-i-made"

    @override
    def describe(self) -> str:
        return (
            "같은 프로젝트에 두 사람이 각자 배포를 만들었고 자기 스코프에서 읽기 권한을 받은 "
            "사람이 자기 것을 훑으면, 자기가 만든 것만 나온다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyDeploymentsAndACaller]:
        return MineBesideAnothers(reads_own=True)

    @override
    def when(self) -> When[ManyDeploymentsAndACaller, DeploymentAdapter, Searched]:
        return SearchingMine()

    @override
    def then(self) -> Then[ManyDeploymentsAndACaller, Searched]:
        return EveryLaidDeploymentIsFound()


@dataclass(frozen=True)
class MyOwnNeedAGrantToo(
    Scenario[SeedingSession, ManyDeploymentsAndACaller, DeploymentAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-even-their-own"

    @override
    def describe(self) -> str:
        return (
            "자기 스코프에서 읽기 권한을 받지 않은 사람이 자기 것을 훑으면, 권한 부족으로 "
            "거부된다. 이 문도 범위를 좁히기만 하지 않고 권한이 지킨다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyDeploymentsAndACaller]:
        return MineBesideAnothers()

    @override
    def when(self) -> When[ManyDeploymentsAndACaller, DeploymentAdapter, Searched]:
        return SearchingMine()

    @override
    def then(self) -> Then[ManyDeploymentsAndACaller, Searched]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[SearchingStep] = [
    TheSuperadminCountsEveryOne(),
    AGrantDoesNotOpenTheGlobalDoor(),
    OnlyThatProjectsOnesAreFound(),
    AProjectWithNoGrantIsRefused(),
    OnlyMyOwnAreFound(),
    MyOwnNeedAGrantToo(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: DeploymentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
