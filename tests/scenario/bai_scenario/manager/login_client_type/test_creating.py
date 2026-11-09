"""로그인 클라이언트 종류 생성 — 누가 생성할 수 있고, 생성된 노드에 무엇이 담기는가.

이름이 비어 있거나 길이 제한을 넘는 요청은 여기 없다. 요청 타입이 이미 막기 때문이다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.login_client_type.request import CreateLoginClientTypeInput
from ai.backend.common.dto.manager.v2.login_client_type.response import LoginClientTypeNode
from ai.backend.manager.api.adapters.login_client_type.adapter import LoginClientTypeAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege, LoginClientTypeConflict
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.login_client_type import (
    ATypeAndACaller,
    ATypeAndSomeone,
    TheNewTypeNode,
)
from bai_scenario.components.system import ENFORCEMENT, ACaller, SomeoneAlone
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

MADE = "webui"
DESCRIBED = Says("새로 지정한 설명", english="the description just set")

type CreatingStep = Scenario[TestSeedingSession, Any, LoginClientTypeAdapter, LoginClientTypeNode]


@dataclass(frozen=True)
class Creating(When[ACaller, LoginClientTypeAdapter, LoginClientTypeNode]):
    """종류 하나를 생성한다. 응답에 담긴 노드를 꺼내서 준다."""

    named: str = MADE
    described: str | None = None

    @override
    def operation(self) -> str:
        return "admin_create"

    @override
    def describe(self, laid: ACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 {self.named} 로그인 클라이언트 유형을 생성합니다",
            english=(f"{laid.caller.username} creates the login client type {self.named}"),
        )

    @override
    async def call(self, adapter: LoginClientTypeAdapter, laid: ACaller) -> LoginClientTypeNode:
        with ActingAs(laid.caller):
            payload = await adapter.admin_create(
                CreateLoginClientTypeInput(name=self.named, description=self.described)
            )
        return payload.login_client_type


@dataclass(frozen=True)
class CreatingWithTheLaidName(When[ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]):
    """미리 만들어 둔 종류와 같은 이름으로 생성한다."""

    @override
    def operation(self) -> str:
        return "admin_create"

    @override
    def describe(self, laid: ATypeAndACaller) -> str:
        return Says(
            (
                f"{laid.caller.username} 이 이미 있는 이름 {laid.client_type.name} (으)로 "
                "로그인 클라이언트 유형을 다시 생성합니다"
            ),
            english=(
                f"{laid.caller.username} creates the login client type again with the existing "
                f"name {laid.client_type.name}"
            ),
        )

    @override
    async def call(
        self, adapter: LoginClientTypeAdapter, laid: ATypeAndACaller
    ) -> LoginClientTypeNode:
        with ActingAs(laid.caller):
            payload = await adapter.admin_create(
                CreateLoginClientTypeInput(name=laid.client_type.name)
            )
        return payload.login_client_type


@dataclass(frozen=True)
class TheSuperadminMakesOneWithANameAlone(
    Scenario[TestSeedingSession, ACaller, LoginClientTypeAdapter, LoginClientTypeNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-makes-a-login-client-type-with-a-name-alone"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 이름만 지정해 로그인 클라이언트 유형을 생성하면 설명이 비어 있는 노드가 "
            "반환됩니다",
            english=(
                "when the superadmin creates a login client type with only a name, the node comes "
                "back with an empty description"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACaller, LoginClientTypeAdapter, LoginClientTypeNode]:
        return Creating()

    @override
    def then(self) -> Then[ACaller, LoginClientTypeNode]:
        return TheNewTypeNode(started=self.started, named=MADE, described=None)


@dataclass(frozen=True)
class ADescriptionComesBackAsGiven(
    Scenario[TestSeedingSession, ACaller, LoginClientTypeAdapter, LoginClientTypeNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-login-client-type-made-with-a-description-carries-it-back"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 이름과 설명을 함께 지정해 로그인 클라이언트 유형을 생성하면 지정한 값이 "
            "그대로 담긴 노드가 반환됩니다",
            english=(
                "when the superadmin creates a login client type with a name and a description, "
                "the node comes back carrying the given values"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACaller, LoginClientTypeAdapter, LoginClientTypeNode]:
        return Creating(described=DESCRIBED)

    @override
    def then(self) -> Then[ACaller, LoginClientTypeNode]:
        return TheNewTypeNode(started=self.started, named=MADE, described=DESCRIBED)


@dataclass(frozen=True)
class ANameAlreadyTakenIsRefused(
    Scenario[TestSeedingSession, ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]
):
    @override
    def summary(self) -> str:
        return "a-login-client-type-name-already-taken-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "같은 이름의 로그인 클라이언트 유형이 이미 있을 때 그 이름으로 다시 생성하면 이름 중복으로 "
            "거부됩니다",
            english=(
                "when a login client type with the same name already exists, creating another with "
                "that name is rejected as a duplicate name"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ATypeAndACaller]:
        return ATypeAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]:
        return CreatingWithTheLaidName()

    @override
    def then(self) -> Then[ATypeAndACaller, LoginClientTypeNode]:
        return TheCallIsRefused(LoginClientTypeConflict)


@dataclass(frozen=True)
class AUserWhoIsNotTheSuperadminMayNotCreate(
    Scenario[TestSeedingSession, ACaller, LoginClientTypeAdapter, LoginClientTypeNode]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-create-a-login-client-type"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 아닌 사용자가 로그인 클라이언트 유형을 생성하면 역할 부족으로 거부됩니다",
            english=(
                "when a user who is not the superadmin creates a login client type, it is rejected "
                "because the role is insufficient"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACaller]:
        return SomeoneAlone()

    @override
    def when(self) -> When[ACaller, LoginClientTypeAdapter, LoginClientTypeNode]:
        return Creating()

    @override
    def then(self) -> Then[ACaller, LoginClientTypeNode]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class EnforcementOffStillNeedsTheSuperadmin(
    Scenario[TestSeedingSession, ACaller, LoginClientTypeAdapter, LoginClientTypeNode], Configured
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-does-not-let-a-user-create-a-login-client-type"

    @override
    def describe(self) -> str:
        return Says(
            "권한 검사를 꺼도 superadmin 이 아니면 로그인 클라이언트 유형을 생성하지 못합니다",
            english=(
                "turning permission enforcement off still does not let a user who is not the "
                "superadmin create a login client type"
            ),
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[TestSeedingSession, ACaller]:
        return SomeoneAlone()

    @override
    def when(self) -> When[ACaller, LoginClientTypeAdapter, LoginClientTypeNode]:
        return Creating()

    @override
    def then(self) -> Then[ACaller, LoginClientTypeNode]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[CreatingStep] = [
    TheSuperadminMakesOneWithANameAlone(started=datetime.now(UTC)),
    ADescriptionComesBackAsGiven(started=datetime.now(UTC)),
    ANameAlreadyTakenIsRefused(),
    AUserWhoIsNotTheSuperadminMayNotCreate(),
    EnforcementOffStillNeedsTheSuperadmin(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: CreatingStep, adapter: LoginClientTypeAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
