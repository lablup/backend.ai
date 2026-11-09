"""설정 정의 등록 — 누가 이름을 등록할 수 있고, 무엇이 이름을 막는가."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.app_config_definition.request import (
    CreateAppConfigDefinitionInput,
)
from ai.backend.common.dto.manager.v2.app_config_definition.response import (
    AppConfigDefinitionNode,
)
from ai.backend.manager.api.adapters.app_config_definition.adapter import (
    AppConfigDefinitionAdapter,
)
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.app_config import ENFORCEMENT
from bai_scenario.components.app_config_definition import (
    ADefinitionAndACaller,
    ADefinitionAndSomeone,
    TheNewDefinitionNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type RegisteringStep = Scenario[
    TestSeedingSession, ADefinitionAndACaller, AppConfigDefinitionAdapter, AppConfigDefinitionNode
]

FRESH = "fresh-config"


@dataclass(frozen=True)
class Registering(When[ADefinitionAndACaller, AppConfigDefinitionAdapter, AppConfigDefinitionNode]):
    """설정 이름을 등록한다. 이름을 지정하지 않으면 미리 만들어 둔 정의의 이름을 그대로 쓴다."""

    named: str | None = None

    @override
    def operation(self) -> str:
        return "admin_create"

    @override
    def describe(self, laid: ADefinitionAndACaller) -> str:
        named = self.named or laid.definition.config_name
        return Says(
            f"{laid.caller.username} 이 설정 이름 {named} 을 등록합니다",
            english=f"{laid.caller.username} registers the config name {named}",
        )

    @override
    async def call(
        self, adapter: AppConfigDefinitionAdapter, laid: ADefinitionAndACaller
    ) -> AppConfigDefinitionNode:
        wanted = self.named or laid.definition.config_name
        with ActingAs(laid.caller):
            payload = await adapter.admin_create(CreateAppConfigDefinitionInput(config_name=wanted))
        return payload.app_config_definition


@dataclass(frozen=True)
class TheSuperadminRegistersAName(
    Scenario[
        TestSeedingSession,
        ADefinitionAndACaller,
        AppConfigDefinitionAdapter,
        AppConfigDefinitionNode,
    ]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-registers-a-name"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 이름만 지정해 설정 정의를 등록하면, 이름은 지정한 그대로이고 ID 와 시각은 "
            "서버가 채운 노드가 반환됩니다",
            english=(
                "when the superadmin registers a config definition with only a name, the node "
                "comes back with the name as given and the id and times filled by the server"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADefinitionAndACaller]:
        return ADefinitionAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[ADefinitionAndACaller, AppConfigDefinitionAdapter, AppConfigDefinitionNode]:
        return Registering(named=FRESH)

    @override
    def then(self) -> Then[ADefinitionAndACaller, AppConfigDefinitionNode]:
        return TheNewDefinitionNode(started=self.started, named=FRESH)


@dataclass(frozen=True)
class ANameAlreadyRegisteredIsRefused(
    Scenario[
        TestSeedingSession,
        ADefinitionAndACaller,
        AppConfigDefinitionAdapter,
        AppConfigDefinitionNode,
    ]
):
    @override
    def summary(self) -> str:
        return "a-name-already-registered-is-refused-as-a-constraint-violation"

    @override
    def describe(self) -> str:
        return Says(
            "이미 등록된 이름으로 superadmin 이 다시 등록하면 거부되지만, 응답이 이름 중복이라고 "
            "알려 주지 않고 데이터베이스의 제약 위반이 그대로 전파됩니다",
            english=(
                "when the superadmin registers again with a name already registered, it is "
                "rejected, but the answer does not say the name is taken and the database "
                "constraint violation propagates as it is"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADefinitionAndACaller]:
        return ADefinitionAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[ADefinitionAndACaller, AppConfigDefinitionAdapter, AppConfigDefinitionNode]:
        return Registering()

    @override
    def then(self) -> Then[ADefinitionAndACaller, AppConfigDefinitionNode]:
        return TheCallIsRefused(UniqueConstraintViolationError)


@dataclass(frozen=True)
class APlainUserMayNotRegister(
    Scenario[
        TestSeedingSession,
        ADefinitionAndACaller,
        AppConfigDefinitionAdapter,
        AppConfigDefinitionNode,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-register-a-name"

    @override
    def describe(self) -> str:
        return Says(
            "일반 사용자가 설정 정의를 등록하려 하면, superadmin 권한이 없어 거부됩니다",
            english=(
                "when a regular user tries to register a config definition, it is rejected "
                "because the user has no superadmin privilege"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADefinitionAndACaller]:
        return ADefinitionAndSomeone()

    @override
    def when(
        self,
    ) -> When[ADefinitionAndACaller, AppConfigDefinitionAdapter, AppConfigDefinitionNode]:
        return Registering(named=FRESH)

    @override
    def then(self) -> Then[ADefinitionAndACaller, AppConfigDefinitionNode]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class EnforcementOffChangesNothing(
    Scenario[
        TestSeedingSession,
        ADefinitionAndACaller,
        AppConfigDefinitionAdapter,
        AppConfigDefinitionNode,
    ],
    Configured,
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-still-does-not-let-a-user-register-a-name"

    @override
    def describe(self) -> str:
        return Says(
            "RBAC 강제를 꺼도 일반 사용자의 설정 정의 등록은 거부됩니다",
            english=(
                "turning RBAC enforcement off still rejects registering a config definition "
                "by a regular user"
            ),
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[TestSeedingSession, ADefinitionAndACaller]:
        return ADefinitionAndSomeone()

    @override
    def when(
        self,
    ) -> When[ADefinitionAndACaller, AppConfigDefinitionAdapter, AppConfigDefinitionNode]:
        return Registering(named=FRESH)

    @override
    def then(self) -> Then[ADefinitionAndACaller, AppConfigDefinitionNode]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[RegisteringStep] = [
    TheSuperadminRegistersAName(started=datetime.now(UTC)),
    ANameAlreadyRegisteredIsRefused(),
    APlainUserMayNotRegister(),
    EnforcementOffChangesNothing(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_registering(
    scenario: RegisteringStep, adapter: AppConfigDefinitionAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
