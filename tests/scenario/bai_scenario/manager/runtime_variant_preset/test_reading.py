"""프리셋 조회 — 하나 또는 여러 ID로 조회하며, 두 방식 모두 인증 여부만 확인한다.

여러 ID 조회는 검색에 ID 조건을 지정하여 실행하므로 존재하지 않는 ID는 빈 항목으로 반환된다.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.runtime_variant_preset import RuntimeVariantPresetID
from ai.backend.common.dto.manager.v2.runtime_variant_preset.response import (
    RuntimeVariantPresetNode,
)
from ai.backend.manager.api.adapters.runtime_variant_preset.adapter import (
    RuntimeVariantPresetAdapter,
)
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Same,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.runtime_variant_preset import (
    APresetAndACaller,
    APresetAndSomeone,
    ManyPresetsAndACaller,
    ManyPresetsAndSomeone,
    ThePresetNode,
    ThePresetsInTheOrderAsked,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type Loaded = list[RuntimeVariantPresetNode | None]
type ReadingStep = Scenario[SeedingSession, Any, RuntimeVariantPresetAdapter, Any]


@dataclass(frozen=True)
class ReadingById(When[APresetAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode]):
    """ID로 조회한다. ``unknown``이면 어느 행에도 없는 ID를 사용한다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: APresetAndACaller) -> str:
        target = "존재하지 않는 ID" if self.unknown else laid.preset.name
        return f"{laid.caller.username}의 조회 요청 — 대상: {target}"

    @override
    async def call(
        self, adapter: RuntimeVariantPresetAdapter, laid: APresetAndACaller
    ) -> RuntimeVariantPresetNode:
        with ActingAs(laid.caller):
            return await adapter.get(uuid4() if self.unknown else laid.preset.id)


@dataclass(frozen=True)
class ReadingManyByIds(When[ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Loaded]):
    """미리 만들어 둔 프리셋들의 ID와 존재하지 않는 ID 하나를 함께 조회한다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        return (
            f"{laid.caller.username}이 미리 만들어 둔 프리셋 {len(laid.laid)}개와 "
            "존재하지 않는 ID 하나를 함께 조회"
        )

    @override
    async def call(
        self, adapter: RuntimeVariantPresetAdapter, laid: ManyPresetsAndACaller
    ) -> Loaded:
        ids: Sequence[RuntimeVariantPresetID] = [
            *(one.id for one in laid.laid),
            RuntimeVariantPresetID(uuid4()),
        ]
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids(ids)


@dataclass(frozen=True)
class ReadingNoIds(When[APresetAndACaller, RuntimeVariantPresetAdapter, Loaded]):
    """빈 ID 목록으로 조회한다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: APresetAndACaller) -> str:
        return f"{laid.caller.username}이 빈 ID 목록으로 조회"

    @override
    async def call(self, adapter: RuntimeVariantPresetAdapter, laid: APresetAndACaller) -> Loaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids([])


@dataclass(frozen=True)
class NothingComesBack(Then[Any, Loaded]):
    """빈 응답이 반환된다."""

    @override
    def says(self) -> str:
        return "빈 응답이 반환된다"

    @override
    def look(self, laid: Any, answered: Answered[Loaded]) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [Same("items", items, [])]


@dataclass(frozen=True)
class AUserGrantedNothingReadsById(
    Scenario[
        SeedingSession, APresetAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode
    ]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-reads-a-preset-by-id"

    @override
    def describe(self) -> str:
        return "아무 권한도 없는 사용자가 ID로 조회해도 해당 프리셋 전체가 반환된다. 이 조회는 인증 여부만 확인한다"

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone()

    @override
    def when(
        self,
    ) -> When[APresetAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode]:
        return ReadingById()

    @override
    def then(self) -> Then[APresetAndACaller, RuntimeVariantPresetNode]:
        return ThePresetNode(started=self.started)


@dataclass(frozen=True)
class AnIdNothingAnswersToIsNotFound(
    Scenario[
        SeedingSession, APresetAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode
    ]
):
    @override
    def summary(self) -> str:
        return "reading-a-preset-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "존재하지 않는 ID로 조회하면 대상을 찾을 수 없어 요청이 거부된다"

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone()

    @override
    def when(
        self,
    ) -> When[APresetAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode]:
        return ReadingById(unknown=True)

    @override
    def then(self) -> Then[APresetAndACaller, RuntimeVariantPresetNode]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class MixedIdsComeBackInOrder(
    Scenario[SeedingSession, ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Loaded]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "presets-read-by-many-ids-come-back-in-the-order-asked"

    @override
    def describe(self) -> str:
        return "존재하는 ID 둘과 존재하지 않는 ID 하나를 함께 조회하면 요청한 순서대로 반환되고, 존재하지 않는 ID의 위치는 비어 있다"

    @override
    def given(self) -> Given[SeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(besides=1)

    @override
    def when(self) -> When[ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Loaded]:
        return ReadingManyByIds()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Loaded]:
        return ThePresetsInTheOrderAsked(started=self.started)


@dataclass(frozen=True)
class AnEmptyListAnswersEmpty(
    Scenario[SeedingSession, APresetAndACaller, RuntimeVariantPresetAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "an-empty-preset-id-list-answers-empty-without-a-call"

    @override
    def describe(self) -> str:
        return "빈 ID 목록으로 조회하면 빈 응답이 반환되며 하위 계층은 호출하지 않는다"

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone()

    @override
    def when(self) -> When[APresetAndACaller, RuntimeVariantPresetAdapter, Loaded]:
        return ReadingNoIds()

    @override
    def then(self) -> Then[APresetAndACaller, Loaded]:
        return NothingComesBack()


SCENARIOS: list[ReadingStep] = [
    AUserGrantedNothingReadsById(started=datetime.now(UTC)),
    AnIdNothingAnswersToIsNotFound(),
    MixedIdsComeBackInOrder(started=datetime.now(UTC)),
    AnEmptyListAnswersEmpty(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadingStep, adapter: RuntimeVariantPresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
