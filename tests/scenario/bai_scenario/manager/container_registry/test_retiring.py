"""레지스트리 지우기 — 되돌릴 수 없고, 연결도 함께 사라진다."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import override
from uuid import UUID

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.container_registry import (
    AnIdThatHoldsNothing,
    ARegistryAndACaller,
    ARegistryAndSomeone,
    Target,
    TheLaidRegistry,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.container_registry.request import (
    DeleteContainerRegistryInput,
)
from ai.backend.common.dto.manager.v2.container_registry.response import (
    DeleteContainerRegistryPayload,
)
from ai.backend.manager.api.adapters.container_registry.adapter import ContainerRegistryAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.image import ContainerRegistryNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    SameAs,
    Scenario,
    Then,
    Verdict,
    When,
)

type Deleted = DeleteContainerRegistryPayload
type RetiringStep = Scenario[SeedingSession, ARegistryAndACaller, ContainerRegistryAdapter, Deleted]


@dataclass(frozen=True)
class Retiring(When[ARegistryAndACaller, ContainerRegistryAdapter, Deleted]):
    """레지스트리를 지운다."""

    at: Target = field(default_factory=TheLaidRegistry)

    @override
    def operation(self) -> str:
        return "admin_delete"

    @override
    def describe(self, laid: ARegistryAndACaller) -> str:
        return f"{laid.caller.username}이 {self.at.says()}를 지움"

    @override
    async def call(self, adapter: ContainerRegistryAdapter, laid: ARegistryAndACaller) -> Deleted:
        target = self.at.id_of(laid)
        with ActingAs(laid.caller):
            return await adapter.admin_delete(DeleteContainerRegistryInput(id=target))


@dataclass(frozen=True)
class TheDeletedIdComesBack(Then[ARegistryAndACaller, Deleted]):
    """지운 id가 답으로 온다."""

    @override
    def says(self) -> str:
        return "지운 id가 답으로 온다"

    @override
    def look(self, laid: ARegistryAndACaller, answered: Answered[Deleted]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [
                Refused(type(answered.raised) if answered.raised else Exception, answered.raised)
            ]
        wanted: UUID = laid.registry.id
        return [Held("id", payload.id, SameAs(wanted, "심은 레지스트리의 id"))]


@dataclass(frozen=True)
class TheRegistryIsGone(
    Scenario[SeedingSession, ARegistryAndACaller, ContainerRegistryAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "deleting-a-registry-answers-with-the-id-it-removed"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 레지스트리를 지우면 지운 id가 답으로 온다"

    @override
    def given(self) -> Given[SeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ARegistryAndACaller, ContainerRegistryAdapter, Deleted]:
        return Retiring()

    @override
    def then(self) -> Then[ARegistryAndACaller, Deleted]:
        return TheDeletedIdComesBack()


@dataclass(frozen=True)
class ALinkedRegistryGoesToo(
    Scenario[SeedingSession, ARegistryAndACaller, ContainerRegistryAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "deleting-a-registry-a-project-is-linked-to-takes-the-link-with-it"

    @override
    def describe(self) -> str:
        return "허용 프로젝트가 딸린 레지스트리를 지우면, 외래 키를 통해 그 연결까지 함께 사라진다"

    @override
    def given(self) -> Given[SeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone(role=UserRole.SUPERADMIN, linked=True)

    @override
    def when(self) -> When[ARegistryAndACaller, ContainerRegistryAdapter, Deleted]:
        return Retiring()

    @override
    def then(self) -> Then[ARegistryAndACaller, Deleted]:
        return TheDeletedIdComesBack()


@dataclass(frozen=True)
class AnIdThatHoldsNothingIsRefused(
    Scenario[SeedingSession, ARegistryAndACaller, ContainerRegistryAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "deleting-an-id-that-holds-no-registry-is-refused"

    @override
    def describe(self) -> str:
        return "아무 레지스트리도 갖지 않은 id를 지우려 하면 대상이 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ARegistryAndACaller, ContainerRegistryAdapter, Deleted]:
        return Retiring(at=AnIdThatHoldsNothing())

    @override
    def then(self) -> Then[ARegistryAndACaller, Deleted]:
        return TheCallIsRefused(ContainerRegistryNotFound)


@dataclass(frozen=True)
class APlainUserMayNotDelete(
    Scenario[SeedingSession, ARegistryAndACaller, ContainerRegistryAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-delete-a-registry"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아닌 사용자가 레지스트리를 지우려 하면 역할로 막힌다"

    @override
    def given(self) -> Given[SeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone()

    @override
    def when(self) -> When[ARegistryAndACaller, ContainerRegistryAdapter, Deleted]:
        return Retiring()

    @override
    def then(self) -> Then[ARegistryAndACaller, Deleted]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[RetiringStep] = [
    TheRegistryIsGone(),
    ALinkedRegistryGoesToo(),
    AnIdThatHoldsNothingIsRefused(),
    APlainUserMayNotDelete(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_retiring(
    scenario: RetiringStep,
    adapter: ContainerRegistryAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
