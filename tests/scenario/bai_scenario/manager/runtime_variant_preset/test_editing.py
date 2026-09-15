"""preset 수정 — 무엇이 바뀌고, 서비스가 저장된 행과 합쳐 무엇을 막으며, 누가 수정할 수 있는가."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, override
from uuid import uuid4

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.runtime_variant_preset import (
    APresetAndACaller,
    APresetAndSomeone,
    ThePresetNode,
)
from bai_scenario.components.system import ENFORCEMENT
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.runtime_variant_preset.request import (
    UpdateRuntimeVariantPresetInput,
)
from ai.backend.common.dto.manager.v2.runtime_variant_preset.response import (
    RuntimeVariantPresetNode,
)
from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import PresetValueType
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.manager.api.adapters.runtime_variant_preset.adapter import (
    RuntimeVariantPresetAdapter,
)
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.resource import RuntimeVariantPresetNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Scenario, Then, When

RENAMED = "renamed"
RERANKED = 7

type EditingStep = Scenario[
    SeedingSession, APresetAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode
]


@dataclass(frozen=True)
class Editing(When[APresetAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode]):
    """미리 만들어 둔 preset을 수정한다. ``changes``에 없는 필드는 요청에 담지 않는다."""

    changes: Mapping[str, Any] = field(default_factory=dict)
    unknown: bool = False

    @override
    def operation(self) -> str:
        return "update"

    @override
    def describe(self, laid: APresetAndACaller) -> str:
        target = "존재하지 않는 id" if self.unknown else laid.preset.name
        changing = ", ".join(self.changes) or "아무것도"
        return f"{laid.caller.username}이 {target}의 {changing} 수정"

    @override
    async def call(
        self, adapter: RuntimeVariantPresetAdapter, laid: APresetAndACaller
    ) -> RuntimeVariantPresetNode:
        with ActingAs(laid.caller):
            payload = await adapter.update(
                UpdateRuntimeVariantPresetInput(
                    id=uuid4() if self.unknown else laid.preset.id, **self.changes
                )
            )
        return payload.preset


@dataclass(frozen=True)
class TheNameChangesAndTheRestStays(
    Scenario[
        SeedingSession, APresetAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode
    ]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "renaming-a-preset-leaves-the-rest-alone"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 preset의 이름만 바꾸면, 이름은 새 값이 되고 나머지는 그대로 유지된다"

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[APresetAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode]:
        return Editing({"name": RENAMED})

    @override
    def then(self) -> Then[APresetAndACaller, RuntimeVariantPresetNode]:
        return ThePresetNode(started=self.started, named=RENAMED)


@dataclass(frozen=True)
class ClearingTheDescription(
    Scenario[
        SeedingSession, APresetAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode
    ]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "clearing-a-preset-description-leaves-it-empty"

    @override
    def describe(self) -> str:
        return "설명이 있는 preset에 설명을 비우는 수정을 하면, 설명이 없어진다"

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[APresetAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode]:
        return Editing({"description": None})

    @override
    def then(self) -> Then[APresetAndACaller, RuntimeVariantPresetNode]:
        return ThePresetNode(started=self.started, described=None)


@dataclass(frozen=True)
class RerankingMovesIt(
    Scenario[
        SeedingSession, APresetAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode
    ]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "editing-a-preset-rank-sets-the-new-rank"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 preset의 순위를 바꾸면 순위가 새 값인 노드가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[APresetAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode]:
        return Editing({"rank": RERANKED})

    @override
    def then(self) -> Then[APresetAndACaller, RuntimeVariantPresetNode]:
        return ThePresetNode(started=self.started, rank=RERANKED)


@dataclass(frozen=True)
class AnEmptyEditChangesNothing(
    Scenario[
        SeedingSession, APresetAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode
    ]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-preset-edit-giving-no-value-changes-nothing"

    @override
    def describe(self) -> str:
        return "값을 하나도 지정하지 않고 수정하면 아무것도 바뀌지 않은 노드가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[APresetAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode]:
        return Editing()

    @override
    def then(self) -> Then[APresetAndACaller, RuntimeVariantPresetNode]:
        return ThePresetNode(started=self.started)


@dataclass(frozen=True)
class FlagOnAnEnvPresetIsRefusedByTheService(
    Scenario[
        SeedingSession, APresetAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode
    ]
):
    @override
    def summary(self) -> str:
        return "changing-only-the-value-type-to-flag-on-an-env-preset-is-refused"

    @override
    def describe(self) -> str:
        return (
            "대상이 env인 preset의 값 종류만 flag로 수정하면 잘못된 입력으로 거부된다. "
            "요청은 대상을 생략했으므로 요청 타입은 통과시키고, 서비스가 저장된 대상과 합쳐 검사한 뒤 막는다"
        )

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[APresetAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode]:
        return Editing({"value_type": PresetValueType.FLAG})

    @override
    def then(self) -> Then[APresetAndACaller, RuntimeVariantPresetNode]:
        return TheCallIsRefused(InvalidAPIParameters)


@dataclass(frozen=True)
class ADefaultThatDoesNotFitTheStoredTypeIsRefused(
    Scenario[
        SeedingSession, APresetAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode
    ]
):
    @override
    def summary(self) -> str:
        return "changing-only-the-default-to-one-that-does-not-fit-the-stored-type-is-refused"

    @override
    def describe(self) -> str:
        return (
            "값 종류가 정수인 preset의 기본값만 숫자 아닌 문자열로 수정하면 잘못된 입력으로 "
            "거부된다. 서비스가 저장된 값 종류를 기준으로 새 기본값을 검사한다"
        )

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(
            role=UserRole.SUPERADMIN, value_type=PresetValueType.INT, default_value="4"
        )

    @override
    def when(
        self,
    ) -> When[APresetAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode]:
        return Editing({"default_value": "four"})

    @override
    def then(self) -> Then[APresetAndACaller, RuntimeVariantPresetNode]:
        return TheCallIsRefused(InvalidAPIParameters)


@dataclass(frozen=True)
class TheSuperadminEditingAnUnknownIdIsNotFound(
    Scenario[
        SeedingSession, APresetAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode
    ]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-editing-a-preset-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 존재하지 않는 id를 수정하면 대상을 찾을 수 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[APresetAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode]:
        return Editing({"name": RENAMED}, unknown=True)

    @override
    def then(self) -> Then[APresetAndACaller, RuntimeVariantPresetNode]:
        return TheCallIsRefused(RuntimeVariantPresetNotFound)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotEdit(
    Scenario[
        SeedingSession, APresetAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-edit-a-preset"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 없는 사용자가 preset을 수정하면 권한 부족으로 거부된다. "
            "preset은 어느 스코프에도 속하지 않아 그 권한을 받을 방법이 없다"
        )

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone()

    @override
    def when(
        self,
    ) -> When[APresetAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode]:
        return Editing({"name": RENAMED})

    @override
    def then(self) -> Then[APresetAndACaller, RuntimeVariantPresetNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class EnforcementOffLetsAnyoneEdit(
    Scenario[
        SeedingSession, APresetAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode
    ],
    Configured,
):
    started: datetime

    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-a-user-edit-a-preset"

    @override
    def describe(self) -> str:
        return (
            "권한 검사를 끄면 아무 권한도 없는 사용자도 preset을 수정할 수 있다. "
            "수정은 역할이 아니라 권한 그래프로 보호되기 때문이다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone()

    @override
    def when(
        self,
    ) -> When[APresetAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode]:
        return Editing({"name": RENAMED})

    @override
    def then(self) -> Then[APresetAndACaller, RuntimeVariantPresetNode]:
        return ThePresetNode(started=self.started, named=RENAMED)


SCENARIOS: list[EditingStep] = [
    TheNameChangesAndTheRestStays(started=datetime.now(UTC)),
    ClearingTheDescription(started=datetime.now(UTC)),
    RerankingMovesIt(started=datetime.now(UTC)),
    AnEmptyEditChangesNothing(started=datetime.now(UTC)),
    FlagOnAnEnvPresetIsRefusedByTheService(),
    ADefaultThatDoesNotFitTheStoredTypeIsRefused(),
    TheSuperadminEditingAnUnknownIdIsNotFound(),
    AUserGrantedNothingMayNotEdit(),
    EnforcementOffLetsAnyoneEdit(started=datetime.now(UTC)),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing(
    scenario: EditingStep, adapter: RuntimeVariantPresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
