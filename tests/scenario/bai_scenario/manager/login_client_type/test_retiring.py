"""로그인 클라이언트 종류 지우기 — 누가 지울 수 있고, 집행을 끄면 무엇이 열리는가."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override
from uuid import uuid4

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.login_client_type import (
    ATypeAndACaller,
    ATypeAndSomeone,
    TheDeletedTypeId,
)
from bai_scenario.components.system import ENFORCEMENT
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.login_client_type.response import (
    DeleteLoginClientTypePayload,
)
from ai.backend.manager.api.adapters.login_client_type.adapter import LoginClientTypeAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Scenario, Then, When

type Deleted = DeleteLoginClientTypePayload
type RetiringStep = Scenario[SeedingSession, ATypeAndACaller, LoginClientTypeAdapter, Deleted]


@dataclass(frozen=True)
class Deleting(When[ATypeAndACaller, LoginClientTypeAdapter, Deleted]):
    """심은 종류 하나를 지운다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "admin_delete"

    @override
    def describe(self, laid: ATypeAndACaller) -> str:
        target = "없는 id" if self.unknown else laid.client_type.name
        return f"{laid.caller.username}이 {target}를 지움"

    @override
    async def call(self, adapter: LoginClientTypeAdapter, laid: ATypeAndACaller) -> Deleted:
        with ActingAs(laid.caller):
            return await adapter.admin_delete(uuid4() if self.unknown else laid.client_type.id)


@dataclass(frozen=True)
class TheSuperadminDeletesAType(
    Scenario[SeedingSession, ATypeAndACaller, LoginClientTypeAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-deletes-a-login-client-type"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 종류를 지우면 지운 종류의 id를 실은 답이 온다"

    @override
    def given(self) -> Given[SeedingSession, ATypeAndACaller]:
        return ATypeAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ATypeAndACaller, LoginClientTypeAdapter, Deleted]:
        return Deleting()

    @override
    def then(self) -> Then[ATypeAndACaller, Deleted]:
        return TheDeletedTypeId()


@dataclass(frozen=True)
class AnIdNothingAnswersToIsNotFound(
    Scenario[SeedingSession, ATypeAndACaller, LoginClientTypeAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "deleting-a-login-client-type-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아무 종류도 갖지 않은 id를 지우면 대상이 없다는 것으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ATypeAndACaller]:
        return ATypeAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ATypeAndACaller, LoginClientTypeAdapter, Deleted]:
        return Deleting(unknown=True)

    @override
    def then(self) -> Then[ATypeAndACaller, Deleted]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotDelete(
    Scenario[SeedingSession, ATypeAndACaller, LoginClientTypeAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-delete-a-login-client-type"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 종류를 지우면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ATypeAndACaller]:
        return ATypeAndSomeone()

    @override
    def when(self) -> When[ATypeAndACaller, LoginClientTypeAdapter, Deleted]:
        return Deleting()

    @override
    def then(self) -> Then[ATypeAndACaller, Deleted]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class EnforcementOffLetsAnyoneDelete(
    Scenario[SeedingSession, ATypeAndACaller, LoginClientTypeAdapter, Deleted], Configured
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-a-user-delete-a-login-client-type"

    @override
    def describe(self) -> str:
        return (
            "엔티티 권한 집행을 끄면 아무 권한도 받지 않은 사용자도 종류를 지운다. "
            "이 문은 역할이 아니라 권한 그래프가 지키기 때문이다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, ATypeAndACaller]:
        return ATypeAndSomeone()

    @override
    def when(self) -> When[ATypeAndACaller, LoginClientTypeAdapter, Deleted]:
        return Deleting()

    @override
    def then(self) -> Then[ATypeAndACaller, Deleted]:
        return TheDeletedTypeId()


SCENARIOS: list[RetiringStep] = [
    TheSuperadminDeletesAType(),
    AnIdNothingAnswersToIsNotFound(),
    AUserGrantedNothingMayNotDelete(),
    EnforcementOffLetsAnyoneDelete(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_retiring(
    scenario: RetiringStep, adapter: LoginClientTypeAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
