"""시스템 세션 환경변수 하나 등록하기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID, uuid4

import pytest

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironScopeID
from ai.backend.common.data.system_session_environ.types import (
    SystemSessionEnvironScopeType,
    SystemSessionEnvironValueSource,
)
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.system_session_environ.request import (
    CreateSystemSessionEnvironInput,
)
from ai.backend.common.dto.manager.v2.system_session_environ.response import (
    CreateSystemSessionEnvironPayload,
    SystemSessionEnvironNode,
)
from ai.backend.manager.api.adapters.system_session_environ.adapter import (
    SystemSessionEnvironAdapter,
)
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.resource import DomainNotFound
from ai.backend.manager.errors.system_session_environ import (
    SystemSessionEnvironKeyConflict,
    UnknownSystemSessionEnvironValueSource,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Same,
    SameAs,
    Says,
    Scenario,
    Skipped,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.domain import WrittenByThisRun
from bai_scenario.components.system import ACaller, SomeoneAlone, lay_a_caller
from bai_scenario.components.system_session_environ import ACallerGrantedInPublic
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.system_session_environ.environ import (
    SEEDED_KEY,
    TestSeedSystemSessionEnviron,
)

CREATED_KEY = "SCENARIO_CREATED_KEY"
CREATED_SOURCE = SystemSessionEnvironValueSource.USER_EMAIL

type CreatingStep = Scenario[
    TestSeedingSession, ACaller, SystemSessionEnvironAdapter, CreateSystemSessionEnvironPayload
]


@dataclass(frozen=True)
class CreatingAtPublic(
    When[ACaller, SystemSessionEnvironAdapter, CreateSystemSessionEnvironPayload]
):
    key: str = CREATED_KEY
    value_source: str = CREATED_SOURCE.value
    scope_type: SystemSessionEnvironScopeType = SystemSessionEnvironScopeType.PUBLIC
    scope_id: SystemSessionEnvironScopeID | None = None

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: ACaller) -> str:
        return Says(
            f"{laid.caller.username}이 시스템 세션 환경변수를 등록합니다",
            english=f"{laid.caller.username} registers a system session environ",
        )

    @override
    async def call(
        self, adapter: SystemSessionEnvironAdapter, laid: ACaller
    ) -> CreateSystemSessionEnvironPayload:
        with ActingAs(laid.caller):
            return await adapter.create(
                CreateSystemSessionEnvironInput(
                    key=self.key,
                    value_source=self.value_source,
                    scope_type=self.scope_type,
                    scope_id=self.scope_id,
                )
            )


@dataclass(frozen=True)
class TheCreatedEnviron(Then[ACaller, CreateSystemSessionEnvironPayload]):
    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "등록한 행 전체가 반환됩니다",
            english="the whole registered row comes back",
        )

    @override
    def look(
        self, laid: ACaller, answered: Answered[CreateSystemSessionEnvironPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        node: SystemSessionEnvironNode = payload.system_session_environ
        written = WrittenByThisRun(self.started)
        return [
            Skipped(
                "entity_id",
                Says("데이터베이스가 생성합니다", english="the database generates it"),
            ),
            Same("key", node.key, CREATED_KEY),
            Same("value_source", node.value_source, CREATED_SOURCE.value),
            Same("scope.scope_type", node.scope.scope_type, SystemSessionEnvironScopeType.PUBLIC),
            Held[UUID](
                "scope.scope_id",
                node.scope.scope_id,
                SameAs[UUID](
                    global_entity_id(GlobalEntityName.PUBLIC),
                    Says("public 범위의 id", english="the id of the public scope"),
                ),
            ),
            Held("created_at", node.created_at, written),
            Held("updated_at", node.updated_at, written),
            Same("deleted_at", node.deleted_at, None),
        ]


@dataclass(frozen=True)
class AUserGrantedCreateRegisters(
    Scenario[
        TestSeedingSession, ACaller, SystemSessionEnvironAdapter, CreateSystemSessionEnvironPayload
    ]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-create-registers-an-environ-in-public"

    @override
    def describe(self) -> str:
        return Says(
            "public 에서 등록 권한을 받은 사용자가 시스템 세션 환경변수를 등록하면 등록한 행 전체가 "
            "반환됩니다",
            english=(
                "when a user granted create permission in public registers a system session "
                "environ, the whole registered row comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACaller]:
        return ACallerGrantedInPublic()

    @override
    def when(self) -> When[ACaller, SystemSessionEnvironAdapter, CreateSystemSessionEnvironPayload]:
        return CreatingAtPublic()

    @override
    def then(self) -> Then[ACaller, CreateSystemSessionEnvironPayload]:
        return TheCreatedEnviron(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotCreate(
    Scenario[
        TestSeedingSession, ACaller, SystemSessionEnvironAdapter, CreateSystemSessionEnvironPayload
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-create-an-environ"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 시스템 세션 환경변수를 등록하려 하면 권한 부족으로 "
            "거부됩니다",
            english=(
                "when a user granted nothing tries to register a system session environ, it is "
                "rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACaller]:
        return SomeoneAlone()

    @override
    def when(self) -> When[ACaller, SystemSessionEnvironAdapter, CreateSystemSessionEnvironPayload]:
        return CreatingAtPublic()

    @override
    def then(self) -> Then[ACaller, CreateSystemSessionEnvironPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnUnknownValueSourceIsRefused(
    Scenario[
        TestSeedingSession, ACaller, SystemSessionEnvironAdapter, CreateSystemSessionEnvironPayload
    ]
):
    @override
    def summary(self) -> str:
        return "registering-an-environ-with-an-unknown-value-source-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "매니저가 모르는 값 출처로 등록하려 하면 거부됩니다",
            english="when a registration names a value source the manager does not know, it is rejected",
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACaller, SystemSessionEnvironAdapter, CreateSystemSessionEnvironPayload]:
        return CreatingAtPublic(value_source="not-a-value-source")

    @override
    def then(self) -> Then[ACaller, CreateSystemSessionEnvironPayload]:
        return TheCallIsRefused(UnknownSystemSessionEnvironValueSource)


@dataclass(frozen=True)
class ADomainNothingAnswersToIsRefused(
    Scenario[
        TestSeedingSession, ACaller, SystemSessionEnvironAdapter, CreateSystemSessionEnvironPayload
    ]
):
    @override
    def summary(self) -> str:
        return "registering-an-environ-at-a-missing-domain-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "없는 도메인에 등록하려 하면 대상을 찾을 수 없다는 이유로 거부됩니다",
            english=(
                "when a registration names a domain that does not exist, it is rejected because "
                "the target cannot be found"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACaller, SystemSessionEnvironAdapter, CreateSystemSessionEnvironPayload]:
        return CreatingAtPublic(
            scope_type=SystemSessionEnvironScopeType.DOMAIN,
            scope_id=SystemSessionEnvironScopeID(uuid4()),
        )

    @override
    def then(self) -> Then[ACaller, CreateSystemSessionEnvironPayload]:
        return TheCallIsRefused(DomainNotFound)


@dataclass(frozen=True)
class AKeyAlreadyHeldIsRefused(
    Scenario[
        TestSeedingSession, ACaller, SystemSessionEnvironAdapter, CreateSystemSessionEnvironPayload
    ]
):
    @override
    def summary(self) -> str:
        return "registering-an-environ-under-a-key-already-held-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "같은 범위에서 이미 쓰이는 이름으로 등록하려 하면 거부됩니다",
            english=(
                "when a registration names a key another row already holds at the same scope, "
                "it is rejected"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACaller]:
        return ASeededKeyAndACaller()

    @override
    def when(self) -> When[ACaller, SystemSessionEnvironAdapter, CreateSystemSessionEnvironPayload]:
        return CreatingAtPublic(key=SEEDED_KEY)

    @override
    def then(self) -> Then[ACaller, CreateSystemSessionEnvironPayload]:
        return TheCallIsRefused(SystemSessionEnvironKeyConflict)


@dataclass(frozen=True)
class ASeededKeyAndACaller(Given[TestSeedingSession, ACaller]):
    """이미 그 이름으로 등록된 행 하나와 superadmin 한 명."""

    @override
    def describe(self) -> str:
        return Says(
            "이미 등록된 행 하나와 superadmin 한 명",
            english="one row already registered and one superadmin",
        )

    @override
    async def lay(self, seeding: TestSeedingSession) -> ACaller:
        await seeding.creating(TestSeedSystemSessionEnviron(key=SEEDED_KEY))
        caller = await lay_a_caller(seeding, UserRole.SUPERADMIN)
        return ACaller(seeding.made(caller))


SCENARIOS: list[CreatingStep] = [
    AUserGrantedCreateRegisters(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotCreate(),
    AnUnknownValueSourceIsRefused(),
    ADomainNothingAnswersToIsRefused(),
    AKeyAlreadyHeldIsRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: CreatingStep,
    adapter: SystemSessionEnvironAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
