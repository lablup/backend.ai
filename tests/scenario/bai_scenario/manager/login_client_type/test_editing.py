"""로그인 클라이언트 종류 고치기 — 무엇이 바뀌고 무엇이 그대로 남으며, 누가 고칠 수 있는가.

고치기는 지목할 id를 요청 밖에서 따로 받는다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import uuid4

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.login_client_type import (
    ATypeAndACaller,
    ATypeAndSomeone,
    ManyTypesAndACaller,
    ManyTypesAndSomeone,
    TheTypeNode,
)
from bai_scenario.components.system import ENFORCEMENT
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.api_handlers import SENTINEL, Sentinel
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.login_client_type.request import UpdateLoginClientTypeInput
from ai.backend.common.dto.manager.v2.login_client_type.response import LoginClientTypeNode
from ai.backend.manager.api.adapters.login_client_type.adapter import LoginClientTypeAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Scenario, Then, When

RENAMED = "renamed"

type EditingStep = Scenario[SeedingSession, Any, LoginClientTypeAdapter, LoginClientTypeNode]


@dataclass(frozen=True)
class Editing(When[ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]):
    """심은 종류를 고친다. 답이 실은 노드를 벗겨서 준다."""

    named: str | None = None
    described: str | Sentinel | None = SENTINEL
    unknown: bool = False

    @override
    def operation(self) -> str:
        return "admin_update"

    @override
    def describe(self, laid: ATypeAndACaller) -> str:
        target = "없는 id" if self.unknown else laid.client_type.name
        changing = []
        if self.named is not None:
            changing.append("이름")
        if not isinstance(self.described, Sentinel):
            changing.append("설명")
        return f"{laid.caller.username}이 {target}의 {' 및 '.join(changing) or '아무것도'} 고침"

    @override
    async def call(
        self, adapter: LoginClientTypeAdapter, laid: ATypeAndACaller
    ) -> LoginClientTypeNode:
        with ActingAs(laid.caller):
            payload = await adapter.admin_update(
                uuid4() if self.unknown else laid.client_type.id,
                UpdateLoginClientTypeInput(name=self.named, description=self.described),
            )
        return payload.login_client_type


@dataclass(frozen=True)
class RenamingToAnothersName(
    When[ManyTypesAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]
):
    """골라낸 하나의 이름을 옆에 있는 다른 종류의 이름으로 바꾼다."""

    @override
    def operation(self) -> str:
        return "admin_update"

    @override
    def describe(self, laid: ManyTypesAndACaller) -> str:
        other = next(one for one in laid.laid if one.id != laid.named.id)
        return f"{laid.caller.username}이 {laid.named.name}의 이름을 {other.name}으로 고침"

    @override
    async def call(
        self, adapter: LoginClientTypeAdapter, laid: ManyTypesAndACaller
    ) -> LoginClientTypeNode:
        other = next(one for one in laid.laid if one.id != laid.named.id)
        with ActingAs(laid.caller):
            payload = await adapter.admin_update(
                laid.named.id, UpdateLoginClientTypeInput(name=other.name)
            )
        return payload.login_client_type


@dataclass(frozen=True)
class TheNameChangesAndTheDescriptionStays(
    Scenario[SeedingSession, ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "renaming-a-login-client-type-leaves-its-description-alone"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 종류의 이름만 바꾸면, 이름은 새 값이 되고 설명은 그대로 남는다"

    @override
    def given(self) -> Given[SeedingSession, ATypeAndACaller]:
        return ATypeAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]:
        return Editing(named=RENAMED)

    @override
    def then(self) -> Then[ATypeAndACaller, LoginClientTypeNode]:
        return TheTypeNode(started=self.started, named=RENAMED)


@dataclass(frozen=True)
class ClearingTheDescription(
    Scenario[SeedingSession, ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "clearing-a-login-client-type-description-leaves-it-empty"

    @override
    def describe(self) -> str:
        return "설명이 있는 종류의 설명을 비우는 수정을 하면, 설명이 없어진다"

    @override
    def given(self) -> Given[SeedingSession, ATypeAndACaller]:
        return ATypeAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]:
        return Editing(described=None)

    @override
    def then(self) -> Then[ATypeAndACaller, LoginClientTypeNode]:
        return TheTypeNode(started=self.started, described=None)


@dataclass(frozen=True)
class AnEmptyEditChangesNothing(
    Scenario[SeedingSession, ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-login-client-type-edit-giving-no-value-changes-nothing"

    @override
    def describe(self) -> str:
        return "값을 하나도 주지 않고 고치면 아무것도 바뀌지 않은 노드가 온다"

    @override
    def given(self) -> Given[SeedingSession, ATypeAndACaller]:
        return ATypeAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]:
        return Editing()

    @override
    def then(self) -> Then[ATypeAndACaller, LoginClientTypeNode]:
        return TheTypeNode(started=self.started)


@dataclass(frozen=True)
class RenamingToATakenNameIsRefused(
    Scenario[SeedingSession, ManyTypesAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]
):
    @override
    def summary(self) -> str:
        return "renaming-a-login-client-type-to-a-name-already-taken-is-refused"

    @override
    def describe(self) -> str:
        return (
            "종류 둘 중 한쪽의 이름을 다른 쪽 이름으로 바꾸면, 이름이 겹친다는 이유로 거부된다. "
            "만들 때와 달리 저장소의 제약 위반이 그대로 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyTypesAndACaller]:
        return ManyTypesAndSomeone(role=UserRole.SUPERADMIN, besides=1)

    @override
    def when(self) -> When[ManyTypesAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]:
        return RenamingToAnothersName()

    @override
    def then(self) -> Then[ManyTypesAndACaller, LoginClientTypeNode]:
        return TheCallIsRefused(UniqueConstraintViolationError)


@dataclass(frozen=True)
class TheSuperadminEditingAnUnknownIdIsNotFound(
    Scenario[SeedingSession, ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-editing-a-login-client-type-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아무 종류도 갖지 않은 id를 고치면 대상이 없다는 것으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ATypeAndACaller]:
        return ATypeAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]:
        return Editing(named=RENAMED, unknown=True)

    @override
    def then(self) -> Then[ATypeAndACaller, LoginClientTypeNode]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotEdit(
    Scenario[SeedingSession, ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-edit-a-login-client-type"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 종류를 고치면 권한 부족으로 거부된다. "
            "종류는 어느 스코프에도 없어 그 권한을 받을 길이 없다"
        )

    @override
    def given(self) -> Given[SeedingSession, ATypeAndACaller]:
        return ATypeAndSomeone()

    @override
    def when(self) -> When[ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]:
        return Editing(named=RENAMED)

    @override
    def then(self) -> Then[ATypeAndACaller, LoginClientTypeNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserGrantedNothingEditingAnUnknownIdIsRefusedForPermission(
    Scenario[SeedingSession, ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-editing-an-unknown-login-client-type-id-is-refused-for-permission"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 없는 id를 고치면 대상 없음이 아니라 권한 부족으로 "
            "거부된다. 권한 검사가 먼저 돌고 없는 행에는 걸린 권한도 없다"
        )

    @override
    def given(self) -> Given[SeedingSession, ATypeAndACaller]:
        return ATypeAndSomeone()

    @override
    def when(self) -> When[ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]:
        return Editing(named=RENAMED, unknown=True)

    @override
    def then(self) -> Then[ATypeAndACaller, LoginClientTypeNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class EnforcementOffLetsAnyoneEdit(
    Scenario[SeedingSession, ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode],
    Configured,
):
    started: datetime

    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-a-user-edit-a-login-client-type"

    @override
    def describe(self) -> str:
        return (
            "엔티티 권한 집행을 끄면 아무 권한도 받지 않은 사용자도 종류를 고친다. "
            "이 문은 역할이 아니라 권한 그래프가 지키기 때문이다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, ATypeAndACaller]:
        return ATypeAndSomeone()

    @override
    def when(self) -> When[ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]:
        return Editing(named=RENAMED)

    @override
    def then(self) -> Then[ATypeAndACaller, LoginClientTypeNode]:
        return TheTypeNode(started=self.started, named=RENAMED)


SCENARIOS: list[EditingStep] = [
    TheNameChangesAndTheDescriptionStays(started=datetime.now(UTC)),
    ClearingTheDescription(started=datetime.now(UTC)),
    AnEmptyEditChangesNothing(started=datetime.now(UTC)),
    RenamingToATakenNameIsRefused(),
    TheSuperadminEditingAnUnknownIdIsNotFound(),
    AUserGrantedNothingMayNotEdit(),
    AUserGrantedNothingEditingAnUnknownIdIsRefusedForPermission(),
    EnforcementOffLetsAnyoneEdit(started=datetime.now(UTC)),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing(
    scenario: EditingStep, adapter: LoginClientTypeAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
