"""프로젝트를 레지스트리에 default로 연결하는 호출과 권한 검사."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.manager.api.adapters.container_registry.adapter import ContainerRegistryAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.association_container_registries_groups.row import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Same,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.container_registry import (
    ARegistryAndAProjectToAllow,
    ARegistryToAllowAndACaller,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type LinkingDefaultScenario = Scenario[
    TestSeedingSession, ARegistryToAllowAndACaller, ContainerRegistryAdapter, None
]


@dataclass(frozen=True)
class LinkingProjectAsDefault(When[ARegistryToAllowAndACaller, ContainerRegistryAdapter, None]):
    @override
    def operation(self) -> str:
        return "link_project_as_default"

    @override
    def describe(self, laid: ARegistryToAllowAndACaller) -> str:
        return f"{laid.caller.username}이 프로젝트를 레지스트리에 default로 연결한다"

    @override
    async def call(
        self, adapter: ContainerRegistryAdapter, laid: ARegistryToAllowAndACaller
    ) -> None:
        with ActingAs(laid.caller):
            await adapter.link_project_as_default(
                ProjectID(laid.project.id), ContainerRegistryID(laid.registry.id)
            )


@dataclass(frozen=True)
class TheLinkIsWritten(Then[ARegistryToAllowAndACaller, None]):
    @override
    def says(self) -> str:
        return "반환값이 없고 예외도 발생하지 않는다"

    @override
    def look(self, laid: ARegistryToAllowAndACaller, answered: Answered[None]) -> list[Verdict]:
        if answered.raised is not None:
            return [Same("raised", answered.raised, None)]
        return [Same("response", answered.response, None)]


@dataclass(frozen=True)
class LinkingWithCreateOnBothScopes(
    Scenario[TestSeedingSession, ARegistryToAllowAndACaller, ContainerRegistryAdapter, None]
):
    @override
    def summary(self) -> str:
        return "create-permission-on-both-scopes-links-a-project-as-its-default"

    @override
    def describe(self) -> str:
        return (
            "레지스트리와 프로젝트 양쪽에 생성 권한을 받은 사용자는 "
            "프로젝트를 레지스트리에 연결하면서 default로 지정할 수 있다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARegistryToAllowAndACaller]:
        return ARegistryAndAProjectToAllow(permissions=(Permission.CREATE,))

    @override
    def when(self) -> When[ARegistryToAllowAndACaller, ContainerRegistryAdapter, None]:
        return LinkingProjectAsDefault()

    @override
    def then(self) -> Then[ARegistryToAllowAndACaller, None]:
        return TheLinkIsWritten()


@dataclass(frozen=True)
class LinkingWithoutProjectPermissionIsRefused(
    Scenario[TestSeedingSession, ARegistryToAllowAndACaller, ContainerRegistryAdapter, None]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-on-the-registry-but-not-the-project-cannot-link-a-default"

    @override
    def describe(self) -> str:
        return (
            "레지스트리에만 권한을 받고 프로젝트에는 받지 못한 사용자가 default로 연결하려 하면, "
            "관계 연산은 지정한 스코프 모두의 권한을 검사하므로 권한 부족으로 거부된다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARegistryToAllowAndACaller]:
        return ARegistryAndAProjectToAllow(on_project=False, permissions=(Permission.CREATE,))

    @override
    def when(self) -> When[ARegistryToAllowAndACaller, ContainerRegistryAdapter, None]:
        return LinkingProjectAsDefault()

    @override
    def then(self) -> Then[ARegistryToAllowAndACaller, None]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[LinkingDefaultScenario] = [
    LinkingWithCreateOnBothScopes(),
    LinkingWithoutProjectPermissionIsRefused(),
]


async def default_link_count(engine: ExtendedAsyncSAEngine) -> int:
    async with engine.begin_readonly_session() as session:
        query = (
            sa.select(sa.func.count())
            .select_from(AssociationContainerRegistriesGroupsRow)
            .where(AssociationContainerRegistriesGroupsRow.is_default.is_(True))
        )
        return int(await session.scalar(query) or 0)


def expected_default_link_count(scenario: LinkingDefaultScenario) -> int:
    match scenario:
        case LinkingWithCreateOnBothScopes():
            return 1
        case _:
            return 0


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_linking_default_project(
    scenario: LinkingDefaultScenario,
    adapter: ContainerRegistryAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
    assert await default_link_count(engine) == expected_default_link_count(scenario)
