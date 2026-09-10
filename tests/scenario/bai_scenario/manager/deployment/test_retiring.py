"""배포 지우기 — 누가 지울 수 있는가.

지우기는 soft-delete다. 지우는 중이라고 표시하고 나머지는 뒤에서 돈다. 이 어댑터에는
완전히 지우는 호출이 없다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID, uuid4

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.deployment import ADeploymentAndACaller, ADeploymentInThatPlace
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.deployment.request import DeleteDeploymentInput
from ai.backend.common.dto.manager.v2.deployment.response import DeleteDeploymentPayload
from ai.backend.manager.api.adapters.deployment.adapter import DeploymentAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.service import EndpointNotFound
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

type RetiringStep = Scenario[
    SeedingSession, ADeploymentAndACaller, DeploymentAdapter, DeleteDeploymentPayload
]


@dataclass(frozen=True)
class Retiring(When[ADeploymentAndACaller, DeploymentAdapter, DeleteDeploymentPayload]):
    """배포 하나를 지운다. id를 대지 않으면 심은 배포를 지운다."""

    other: UUID | None = None

    @override
    def operation(self) -> str:
        return "delete"

    @override
    def describe(self, laid: ADeploymentAndACaller) -> str:
        called = (
            "아무것도 갖지 않은 id" if self.other is not None else laid.deployment.metadata.name
        )
        return f"{laid.caller.username}이 {called}를 지움"

    @override
    async def call(
        self, adapter: DeploymentAdapter, laid: ADeploymentAndACaller
    ) -> DeleteDeploymentPayload:
        wanted = self.other if self.other is not None else laid.deployment.id
        with ActingAs(laid.caller):
            return await adapter.delete(DeleteDeploymentInput(id=wanted))


@dataclass(frozen=True)
class TheRetiredOneIsNamed(Then[ADeploymentAndACaller, DeleteDeploymentPayload]):
    """지우기 시작한 배포가 무엇인지 답한다."""

    @override
    def says(self) -> str:
        return "지우기 시작한 배포를 답한다"

    @override
    def look(
        self, laid: ADeploymentAndACaller, answered: Answered[DeleteDeploymentPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [Held("id", payload.id, SameAs[UUID](laid.deployment.id, "심은 배포"))]


@dataclass(frozen=True)
class TheGrantedUserRetiresIt(
    Scenario[SeedingSession, ADeploymentAndACaller, DeploymentAdapter, DeleteDeploymentPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-soft-delete-retires-a-deployment"

    @override
    def describe(self) -> str:
        return "soft-delete 권한을 받은 사용자가 배포를 지우면, 그 배포를 지우기 시작했다고 답한다"

    @override
    def given(self) -> Given[SeedingSession, ADeploymentAndACaller]:
        return ADeploymentInThatPlace(granted=(Permission.SOFT_DELETE,))

    @override
    def when(self) -> When[ADeploymentAndACaller, DeploymentAdapter, DeleteDeploymentPayload]:
        return Retiring()

    @override
    def then(self) -> Then[ADeploymentAndACaller, DeleteDeploymentPayload]:
        return TheRetiredOneIsNamed()


@dataclass(frozen=True)
class UpdatingIsNotEnoughToRetire(
    Scenario[SeedingSession, ADeploymentAndACaller, DeploymentAdapter, DeleteDeploymentPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-only-update-may-not-retire-a-deployment"

    @override
    def describe(self) -> str:
        return (
            "수정 권한만 받고 soft-delete 권한은 받지 않은 사용자가 배포를 지우면, "
            "권한 부족으로 거부된다. 지우기는 수정과 다른 문이다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADeploymentAndACaller]:
        return ADeploymentInThatPlace(granted=(Permission.UPDATE,))

    @override
    def when(self) -> When[ADeploymentAndACaller, DeploymentAdapter, DeleteDeploymentPayload]:
        return Retiring()

    @override
    def then(self) -> Then[ADeploymentAndACaller, DeleteDeploymentPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class RetiringAnUnknownIdIsNotFoundForASuperadmin(
    Scenario[SeedingSession, ADeploymentAndACaller, DeploymentAdapter, DeleteDeploymentPayload]
):
    @override
    def summary(self) -> str:
        return "retiring-an-id-nothing-answers-to-is-not-found-for-a-superadmin"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아무것도 갖지 않은 id를 지우면, 대상이 없다는 것으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ADeploymentAndACaller]:
        return ADeploymentInThatPlace(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ADeploymentAndACaller, DeploymentAdapter, DeleteDeploymentPayload]:
        return Retiring(other=uuid4())

    @override
    def then(self) -> Then[ADeploymentAndACaller, DeleteDeploymentPayload]:
        return TheCallIsRefused(EndpointNotFound)


SCENARIOS: list[RetiringStep] = [
    TheGrantedUserRetiresIt(),
    UpdatingIsNotEnoughToRetire(),
    RetiringAnUnknownIdIsNotFoundForASuperadmin(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_retiring(
    scenario: RetiringStep, adapter: DeploymentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
