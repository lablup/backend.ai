"""허용 프로젝트 붙이고 떼기 — 이 어댑터에서 권한 그래프가 지키는 유일한 자리."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.container_registry import (
    ARegistryAProjectAndACaller,
    ARegistryAProjectAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.container_registry import AllowedGroupsModel
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.manager.api.adapters.container_registry.adapter import ContainerRegistryAdapter
from ai.backend.manager.errors.image import ContainerRegistryGroupsAssociationNotFound
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Configured,
    Given,
    Refused,
    Same,
    Scenario,
    Then,
    Verdict,
    When,
)

ENFORCEMENT = "manager.rbac.enforcement_enabled"
MISSING_PROJECT = "00000000-0000-0000-0000-0000000000ff"

type AllowingStep = Scenario[
    SeedingSession, ARegistryAProjectAndACaller, ContainerRegistryAdapter, None
]


@dataclass(frozen=True)
class Allowing(When[ARegistryAProjectAndACaller, ContainerRegistryAdapter, None]):
    """허용 목록을 고친다. 넣을 것과 뺄 것을 함께 준다."""

    adding: bool = False
    removing: bool = False
    at_missing: bool = False

    @override
    def operation(self) -> str:
        return "apply_allowed_groups"

    @override
    def describe(self, laid: ARegistryAProjectAndACaller) -> str:
        who = laid.caller.username
        if self.at_missing:
            return f"{who}이 없는 프로젝트를 허용 목록에 넣음"
        if self.removing:
            return f"{who}이 {laid.project.name}을 허용 목록에서 뺌"
        return f"{who}이 {laid.project.name}을 허용 목록에 넣음"

    @override
    async def call(
        self, adapter: ContainerRegistryAdapter, laid: ARegistryAProjectAndACaller
    ) -> None:
        named = MISSING_PROJECT if self.at_missing else str(laid.project.id)
        with ActingAs(laid.caller):
            return await adapter.apply_allowed_groups(
                ContainerRegistryID(laid.registry.id),
                AllowedGroupsModel(
                    add=[named] if self.adding or self.at_missing else [],
                    remove=[named] if self.removing else [],
                ),
            )


@dataclass(frozen=True)
class TheCallReturnsNothing(Then[ARegistryAProjectAndACaller, None]):
    """이 호출은 답을 싣지 않는다. 예외 없이 끝나는 것이 성공이다."""

    @override
    def says(self) -> str:
        return "답이 없고 예외도 없다"

    @override
    def look(self, laid: ARegistryAProjectAndACaller, answered: Answered[None]) -> list[Verdict]:
        if answered.raised is not None:
            return [Refused(type(answered.raised), answered.raised)]
        return [Same("response", answered.response, None)]


@dataclass(frozen=True)
class AProjectIsLinked(
    Scenario[SeedingSession, ARegistryAProjectAndACaller, ContainerRegistryAdapter, None]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-on-both-scopes-links-a-project-to-a-registry"

    @override
    def describe(self) -> str:
        return (
            "레지스트리와 프로젝트 두 스코프 모두에 권한을 받은 사용자가 "
            "그 프로젝트를 허용 목록에 넣으면 연결이 만들어진다"
        )

    @override
    def given(self) -> Given[SeedingSession, ARegistryAProjectAndACaller]:
        return ARegistryAProjectAndSomeone()

    @override
    def when(self) -> When[ARegistryAProjectAndACaller, ContainerRegistryAdapter, None]:
        return Allowing(adding=True)

    @override
    def then(self) -> Then[ARegistryAProjectAndACaller, None]:
        return TheCallReturnsNothing()


@dataclass(frozen=True)
class LinkingTwiceIsNotAnError(
    Scenario[SeedingSession, ARegistryAProjectAndACaller, ContainerRegistryAdapter, None]
):
    @override
    def summary(self) -> str:
        return "linking-a-project-that-is-already-linked-is-not-an-error"

    @override
    def describe(self) -> str:
        return (
            "이미 연결된 프로젝트를 다시 허용 목록에 넣어도, "
            "그 쌍은 데이터베이스에서 건너뛰므로 오류가 아니다"
        )

    @override
    def given(self) -> Given[SeedingSession, ARegistryAProjectAndACaller]:
        return ARegistryAProjectAndSomeone(linked=True)

    @override
    def when(self) -> When[ARegistryAProjectAndACaller, ContainerRegistryAdapter, None]:
        return Allowing(adding=True)

    @override
    def then(self) -> Then[ARegistryAProjectAndACaller, None]:
        return TheCallReturnsNothing()


@dataclass(frozen=True)
class ALinkedProjectIsRemoved(
    Scenario[SeedingSession, ARegistryAProjectAndACaller, ContainerRegistryAdapter, None]
):
    @override
    def summary(self) -> str:
        return "a-linked-project-is-removed-from-the-allowed-list"

    @override
    def describe(self) -> str:
        return "이미 연결된 프로젝트를 허용 목록에서 빼면 그 연결이 사라진다"

    @override
    def given(self) -> Given[SeedingSession, ARegistryAProjectAndACaller]:
        return ARegistryAProjectAndSomeone(linked=True)

    @override
    def when(self) -> When[ARegistryAProjectAndACaller, ContainerRegistryAdapter, None]:
        return Allowing(removing=True)

    @override
    def then(self) -> Then[ARegistryAProjectAndACaller, None]:
        return TheCallReturnsNothing()


@dataclass(frozen=True)
class AProjectThatIsNotThereIsRefused(
    Scenario[SeedingSession, ARegistryAProjectAndACaller, ContainerRegistryAdapter, None]
):
    @override
    def summary(self) -> str:
        return "a-project-that-does-not-exist-may-not-be-allowed"

    @override
    def describe(self) -> str:
        return (
            "존재하지 않는 프로젝트를 허용 목록에 넣으려 하면 그 프로젝트가 없다는 이유로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, ARegistryAProjectAndACaller]:
        return ARegistryAProjectAndSomeone()

    @override
    def when(self) -> When[ARegistryAProjectAndACaller, ContainerRegistryAdapter, None]:
        return Allowing(at_missing=True)

    @override
    def then(self) -> Then[ARegistryAProjectAndACaller, None]:
        return TheCallIsRefused(ProjectNotFound)


@dataclass(frozen=True)
class RemovingWhatIsNotLinkedIsRefused(
    Scenario[SeedingSession, ARegistryAProjectAndACaller, ContainerRegistryAdapter, None]
):
    @override
    def summary(self) -> str:
        return "removing-a-project-that-was-never-linked-is-refused"

    @override
    def describe(self) -> str:
        return "지목한 프로젝트 중 실제로 연결된 것이 하나도 없으면, 뺄 것이 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ARegistryAProjectAndACaller]:
        return ARegistryAProjectAndSomeone()

    @override
    def when(self) -> When[ARegistryAProjectAndACaller, ContainerRegistryAdapter, None]:
        return Allowing(removing=True)

    @override
    def then(self) -> Then[ARegistryAProjectAndACaller, None]:
        return TheCallIsRefused(ContainerRegistryGroupsAssociationNotFound)


@dataclass(frozen=True)
class OneScopeIsNotEnough(
    Scenario[SeedingSession, ARegistryAProjectAndACaller, ContainerRegistryAdapter, None]
):
    @override
    def summary(self) -> str:
        return "holding-only-one-of-the-two-scopes-is-not-enough-to-link"

    @override
    def describe(self) -> str:
        return (
            "레지스트리에만 권한을 받고 프로젝트에는 받지 못한 사용자가 연결하려 하면, "
            "관계 동작은 지목한 스코프를 모두 보므로 권한 부족으로 막힌다"
        )

    @override
    def given(self) -> Given[SeedingSession, ARegistryAProjectAndACaller]:
        return ARegistryAProjectAndSomeone(on_project=False)

    @override
    def when(self) -> When[ARegistryAProjectAndACaller, ContainerRegistryAdapter, None]:
        return Allowing(adding=True)

    @override
    def then(self) -> Then[ARegistryAProjectAndACaller, None]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class EnforcementOffOpensThisGate(
    Scenario[SeedingSession, ARegistryAProjectAndACaller, ContainerRegistryAdapter, None],
    Configured,
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-an-ungranted-user-link-a-project"

    @override
    def describe(self) -> str:
        return (
            "엔티티 권한 집행을 끄면 아무 권한도 받지 않은 사용자도 연결할 수 있다. "
            "이 문은 역할이 아니라 권한 그래프가 지키기 때문이다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, ARegistryAProjectAndACaller]:
        return ARegistryAProjectAndSomeone(on_registry=False, on_project=False)

    @override
    def when(self) -> When[ARegistryAProjectAndACaller, ContainerRegistryAdapter, None]:
        return Allowing(adding=True)

    @override
    def then(self) -> Then[ARegistryAProjectAndACaller, None]:
        return TheCallReturnsNothing()


SCENARIOS: list[AllowingStep] = [
    AProjectIsLinked(),
    LinkingTwiceIsNotAnError(),
    ALinkedProjectIsRemoved(),
    AProjectThatIsNotThereIsRefused(),
    RemovingWhatIsNotLinkedIsRefused(),
    OneScopeIsNotEnough(),
    EnforcementOffOpensThisGate(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_allowing(
    scenario: AllowingStep,
    adapter: ContainerRegistryAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
