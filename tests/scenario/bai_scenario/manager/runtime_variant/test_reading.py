"""런타임 변형 읽기 — id로, 이름으로, 여러 id로. 셋 다 인증만 본다."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import UUID, uuid4

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.runtime_variant import (
    AVariantAndACaller,
    AVariantAndSomeone,
    ManyVariantsAndACaller,
    ManyVariantsAndSomeone,
    TheVariantNode,
    TheVariantsInTheOrderAsked,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.dto.manager.v2.runtime_variant.response import RuntimeVariantNode
from ai.backend.manager.api.adapters.runtime_variant.adapter import RuntimeVariantAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Scenario,
    Then,
    Verdict,
    When,
)

type Loaded = list[RuntimeVariantNode | Exception | None]
type ReadingStep = Scenario[SeedingSession, Any, RuntimeVariantAdapter, Any]


@dataclass(frozen=True)
class ReadingById(When[AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]):
    """id로 읽는다. 없는 id를 대면 아무 행도 갖지 않은 id를 쓴다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: AVariantAndACaller) -> str:
        target = "없는 id" if self.unknown else laid.variant.name
        return f"{laid.caller.username}이 {target}로 조회"

    @override
    async def call(
        self, adapter: RuntimeVariantAdapter, laid: AVariantAndACaller
    ) -> RuntimeVariantNode:
        with ActingAs(laid.caller):
            return await adapter.get(uuid4() if self.unknown else laid.variant.id)


@dataclass(frozen=True)
class ResolvingByName(When[AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantID]):
    """이름을 id로 해석한다. 이름을 대지 않으면 심은 변형의 이름을 쓴다."""

    named: str | None = None

    @override
    def operation(self) -> str:
        return "resolve_by_name"

    @override
    def describe(self, laid: AVariantAndACaller) -> str:
        return f"{laid.caller.username}이 {self.named or laid.variant.name}을 id로 해석"

    @override
    async def call(
        self, adapter: RuntimeVariantAdapter, laid: AVariantAndACaller
    ) -> RuntimeVariantID:
        with ActingAs(laid.caller):
            return await adapter.resolve_by_name(self.named or laid.variant.name)


@dataclass(frozen=True)
class ReadingManyByIds(When[ManyVariantsAndACaller, RuntimeVariantAdapter, Loaded]):
    """심은 것들의 id 뒤에 없는 id 하나를 붙여 한 번에 읽는다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: ManyVariantsAndACaller) -> str:
        return f"{laid.caller.username}이 심은 {len(laid.laid)}개와 없는 id 하나를 한 번에 조회"

    @override
    async def call(self, adapter: RuntimeVariantAdapter, laid: ManyVariantsAndACaller) -> Loaded:
        ids: Sequence[RuntimeVariantID] = [
            *(one.id for one in laid.laid),
            RuntimeVariantID(uuid4()),
        ]
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids(ids)


@dataclass(frozen=True)
class ReadingNoIds(When[AVariantAndACaller, RuntimeVariantAdapter, Loaded]):
    """빈 id 목록으로 읽는다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: AVariantAndACaller) -> str:
        return f"{laid.caller.username}이 빈 id 목록으로 조회"

    @override
    async def call(self, adapter: RuntimeVariantAdapter, laid: AVariantAndACaller) -> Loaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids([])


@dataclass(frozen=True)
class TheLaidVariantsId(Then[AVariantAndACaller, RuntimeVariantID]):
    """심은 변형의 id가 온다."""

    @override
    def says(self) -> str:
        return "심은 변형의 id가 온다"

    @override
    def look(self, laid: AVariantAndACaller, answered: Answered[RuntimeVariantID]) -> list[Verdict]:
        resolved = answered.response
        if resolved is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [Held[UUID]("id", resolved, SameAs[UUID](laid.variant.id, "심은 변형"))]


@dataclass(frozen=True)
class NothingComesBack(Then[Any, Loaded]):
    """빈 답이 온다."""

    @override
    def says(self) -> str:
        return "빈 답이 온다"

    @override
    def look(self, laid: Any, answered: Answered[Loaded]) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [Same("items", items, [])]


@dataclass(frozen=True)
class AUserGrantedNothingReadsById(
    Scenario[SeedingSession, AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-reads-a-variant-by-id"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 id로 조회하면, 그 변형 전체가 온다. 이 읽기는 인증만 본다"

    @override
    def given(self) -> Given[SeedingSession, AVariantAndACaller]:
        return AVariantAndSomeone()

    @override
    def when(self) -> When[AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]:
        return ReadingById()

    @override
    def then(self) -> Then[AVariantAndACaller, RuntimeVariantNode]:
        return TheVariantNode(started=self.started)


@dataclass(frozen=True)
class AnIdNothingAnswersToIsNotFound(
    Scenario[SeedingSession, AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]
):
    @override
    def summary(self) -> str:
        return "reading-a-variant-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "아무 변형도 갖지 않은 id로 조회하면 대상이 없다는 것으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AVariantAndACaller]:
        return AVariantAndSomeone()

    @override
    def when(self) -> When[AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]:
        return ReadingById(unknown=True)

    @override
    def then(self) -> Then[AVariantAndACaller, RuntimeVariantNode]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class ANameResolvesToItsId(
    Scenario[SeedingSession, AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantID]
):
    @override
    def summary(self) -> str:
        return "a-variant-name-resolves-to-its-id-for-any-user"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 이름을 해석하면 그 변형의 id가 온다"

    @override
    def given(self) -> Given[SeedingSession, AVariantAndACaller]:
        return AVariantAndSomeone()

    @override
    def when(self) -> When[AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantID]:
        return ResolvingByName()

    @override
    def then(self) -> Then[AVariantAndACaller, RuntimeVariantID]:
        return TheLaidVariantsId()


@dataclass(frozen=True)
class ANameNothingAnswersToIsNotFound(
    Scenario[SeedingSession, AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantID]
):
    @override
    def summary(self) -> str:
        return "resolving-a-variant-name-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return (
            "아무 변형도 갖지 않은 이름을 해석하면 대상이 없다는 것으로 거부된다. "
            "이 해석에는 뒤따르는 권한 검사가 없어 없다는 사실이 그대로 드러난다"
        )

    @override
    def given(self) -> Given[SeedingSession, AVariantAndACaller]:
        return AVariantAndSomeone()

    @override
    def when(self) -> When[AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantID]:
        return ResolvingByName(named="no-such-variant")

    @override
    def then(self) -> Then[AVariantAndACaller, RuntimeVariantID]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class MixedIdsComeBackInOrder(
    Scenario[SeedingSession, ManyVariantsAndACaller, RuntimeVariantAdapter, Loaded]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "variants-read-by-many-ids-come-back-in-the-order-asked"

    @override
    def describe(self) -> str:
        return "있는 id 둘과 없는 id 하나를 한 번에 읽으면, 준 순서대로 오고 없는 id 자리는 비어서 온다"

    @override
    def given(self) -> Given[SeedingSession, ManyVariantsAndACaller]:
        return ManyVariantsAndSomeone(besides=1)

    @override
    def when(self) -> When[ManyVariantsAndACaller, RuntimeVariantAdapter, Loaded]:
        return ReadingManyByIds()

    @override
    def then(self) -> Then[ManyVariantsAndACaller, Loaded]:
        return TheVariantsInTheOrderAsked(started=self.started)


@dataclass(frozen=True)
class AnEmptyListAnswersEmpty(
    Scenario[SeedingSession, AVariantAndACaller, RuntimeVariantAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "an-empty-id-list-answers-empty-without-a-call"

    @override
    def describe(self) -> str:
        return "빈 id 목록을 주면 빈 답이 온다. 배선을 부르지 않는다"

    @override
    def given(self) -> Given[SeedingSession, AVariantAndACaller]:
        return AVariantAndSomeone()

    @override
    def when(self) -> When[AVariantAndACaller, RuntimeVariantAdapter, Loaded]:
        return ReadingNoIds()

    @override
    def then(self) -> Then[AVariantAndACaller, Loaded]:
        return NothingComesBack()


SCENARIOS: list[ReadingStep] = [
    AUserGrantedNothingReadsById(started=datetime.now(UTC)),
    AnIdNothingAnswersToIsNotFound(),
    ANameResolvesToItsId(),
    ANameNothingAnswersToIsNotFound(),
    MixedIdsComeBackInOrder(started=datetime.now(UTC)),
    AnEmptyListAnswersEmpty(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadingStep, adapter: RuntimeVariantAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
