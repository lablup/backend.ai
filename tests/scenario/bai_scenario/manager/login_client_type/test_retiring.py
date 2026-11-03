"""로그인 클라이언트 종류 삭제 — 누가 삭제할 수 있는가."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override
from uuid import uuid4

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.login_client_type.response import (
    PurgeLoginClientTypePayload,
)
from ai.backend.manager.api.adapters.login_client_type.adapter import LoginClientTypeAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.login_client_type import (
    ATypeAndACaller,
    ATypeAndSomeone,
    TheDeletedTypeId,
)
from bai_scenario.components.system import ENFORCEMENT
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Deleted = PurgeLoginClientTypePayload
type RetiringStep = Scenario[TestSeedingSession, ATypeAndACaller, LoginClientTypeAdapter, Deleted]


@dataclass(frozen=True)
class Deleting(When[ATypeAndACaller, LoginClientTypeAdapter, Deleted]):
    """미리 만들어 둔 종류 하나를 삭제한다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "purge"

    @override
    def describe(self, laid: ATypeAndACaller) -> str:
        if self.unknown:
            target_ko = "존재하지 않는 id"
            target_en = "an id nothing answers to"
        else:
            target_ko = laid.client_type.name
            target_en = laid.client_type.name
        return Says(
            f"{laid.caller.username} 이 {target_ko}를 삭제합니다",
            english=f"{laid.caller.username} deletes {target_en}",
        )

    @override
    async def call(self, adapter: LoginClientTypeAdapter, laid: ATypeAndACaller) -> Deleted:
        with ActingAs(laid.caller):
            return await adapter.purge(uuid4() if self.unknown else laid.client_type.id)


@dataclass(frozen=True)
class TheSuperadminDeletesAType(
    Scenario[TestSeedingSession, ATypeAndACaller, LoginClientTypeAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-deletes-a-login-client-type"

    @override
    def describe(self) -> str:
        return Says(
            (
                "superadmin 이 로그인 클라이언트 유형을 삭제하면 삭제한 유형의 id 를 담은 응답이 "
                "반환됩니다"
            ),
            english=(
                "when the superadmin deletes a login client type, a response comes back carrying "
                "the id of the deleted type"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ATypeAndACaller]:
        return ATypeAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ATypeAndACaller, LoginClientTypeAdapter, Deleted]:
        return Deleting()

    @override
    def then(self) -> Then[ATypeAndACaller, Deleted]:
        return TheDeletedTypeId()


@dataclass(frozen=True)
class AnIdNothingAnswersToIsNotFound(
    Scenario[TestSeedingSession, ATypeAndACaller, LoginClientTypeAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "deleting-a-login-client-type-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return Says(
            ("superadmin 이 존재하지 않는 id 를 삭제하면 대상을 찾을 수 없다는 이유로 거부됩니다"),
            english=(
                "when the superadmin deletes an id nothing answers to, it is rejected because the "
                "target cannot be found"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ATypeAndACaller]:
        return ATypeAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ATypeAndACaller, LoginClientTypeAdapter, Deleted]:
        return Deleting(unknown=True)

    @override
    def then(self) -> Then[ATypeAndACaller, Deleted]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotDelete(
    Scenario[TestSeedingSession, ATypeAndACaller, LoginClientTypeAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-delete-a-login-client-type"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 로그인 클라이언트 유형을 삭제하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing deletes a login client type, it is rejected for a "
                "lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ATypeAndACaller]:
        return ATypeAndSomeone()

    @override
    def when(self) -> When[ATypeAndACaller, LoginClientTypeAdapter, Deleted]:
        return Deleting()

    @override
    def then(self) -> Then[ATypeAndACaller, Deleted]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class EnforcementOffLetsAnyoneDelete(
    Scenario[TestSeedingSession, ATypeAndACaller, LoginClientTypeAdapter, Deleted], Configured
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-a-user-delete-a-login-client-type"

    @override
    def describe(self) -> str:
        return Says(
            (
                "권한 검사를 끄면 아무 권한도 없는 사용자도 로그인 클라이언트 유형을 삭제할 수 "
                "있습니다"
            ),
            english=(
                "turning permission enforcement off lets even a user granted nothing delete a "
                "login client type"
            ),
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[TestSeedingSession, ATypeAndACaller]:
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
