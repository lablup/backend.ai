"""리소스 프리셋 읽기 — 하나씩, 그리고 id 여럿을 한 번에."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.entity.resource_preset import ResourcePresetID
from ai.backend.common.dto.manager.v2.resource_preset.response import ResourcePresetNode
from ai.backend.manager.api.adapters.resource_preset.adapter import ResourcePresetAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Same,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.resource_preset import (
    APresetAndACaller,
    APresetAndSomeone,
    ManyPresetsAndACaller,
    ManyPresetsAndSomeone,
    ThePresetNode,
    preset_verdicts,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Loaded = list[ResourcePresetNode | Exception | None]

type ReadingStep = Scenario[
    TestSeedingSession, APresetAndACaller, ResourcePresetAdapter, ResourcePresetNode
]
type LoadingStep = Scenario[
    TestSeedingSession, ManyPresetsAndACaller, ResourcePresetAdapter, Loaded
]


@dataclass(frozen=True)
class ReadingTheId(When[APresetAndACaller, ResourcePresetAdapter, ResourcePresetNode]):
    """미리 만들어 둔 프리셋을 id 로 읽는다."""

    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: APresetAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.preset.name}의 프리셋을 읽습니다",
            english=f"{laid.caller.username} reads the preset of {laid.preset.name}",
        )

    @override
    async def call(
        self, adapter: ResourcePresetAdapter, laid: APresetAndACaller
    ) -> ResourcePresetNode:
        with ActingAs(laid.caller):
            return await adapter.get(laid.preset.id)


@dataclass(frozen=True)
class ReadingSeveralIds(When[ManyPresetsAndACaller, ResourcePresetAdapter, Loaded]):
    """미리 만들어 둔 프리셋들의 id 로 여럿을 읽는다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 프리셋 {len(laid.laid)}개의 id 로 여럿을 읽습니다",
            english=f"{laid.caller.username} reads several presets by the ids of {len(laid.laid)}",
        )

    @override
    async def call(self, adapter: ResourcePresetAdapter, laid: ManyPresetsAndACaller) -> Loaded:
        ids = [ResourcePresetID(one.id) for one in laid.laid]
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids(ids)


@dataclass(frozen=True)
class ThePresetsInTheOrderAsked(Then[ManyPresetsAndACaller, Loaded]):
    """요청한 순서대로 프리셋 전체가 온다."""

    @override
    def says(self) -> str:
        return Says(
            "요청한 순서대로 프리셋 전체가 응답으로 옵니다",
            english="every preset comes back in the order requested",
        )

    @override
    def look(self, laid: ManyPresetsAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [MissingResponse(answered.raised)]
        expected = len(laid.laid)
        if len(items) != expected:
            return [Same("len(items)", len(items), expected)]
        seen: list[Verdict] = [Same("len(items)", len(items), expected)]
        for i, preset in enumerate(laid.laid):
            node = items[i]
            if not isinstance(node, ResourcePresetNode):
                seen.append(Same(f"items[{i}]", type(node).__name__, Says("노드", english="node")))
                continue
            seen += preset_verdicts(f"items[{i}].", node, preset)
        return seen


@dataclass(frozen=True)
class EveryItemIsRefused(Then[ManyPresetsAndACaller, Loaded]):
    """물은 자리마다 권한 부족 거부가 온다. 호출 전체는 답한다."""

    @override
    def says(self) -> str:
        return Says(
            "물은 자리마다 권한 부족 거부가 응답으로 옵니다",
            english="every item asked comes back carrying a denial for not enough permission",
        )

    @override
    def look(self, laid: ManyPresetsAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [MissingResponse(answered.raised)]
        seen: list[Verdict] = [Same("len(items)", len(items), len(laid.laid))]
        for i in range(len(laid.laid)):
            got = items[i] if i < len(items) else None
            seen.append(
                Refused(NotEnoughPermission, got if isinstance(got, BaseException) else None)
            )
        return seen


@dataclass(frozen=True)
class AUserGrantedReadReadsAPreset(
    Scenario[TestSeedingSession, APresetAndACaller, ResourcePresetAdapter, ResourcePresetNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-in-public-reads-a-preset"

    @override
    def describe(self) -> str:
        return Says(
            "public 에서 조회 권한을 받은 사용자가 id 로 프리셋 하나를 읽으면, 그 프리셋 전체가 "
            "반환됩니다",
            english=(
                "a user granted read in public reading one preset by id gets the whole preset"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone(granted=Permission.READ)

    @override
    def when(self) -> When[APresetAndACaller, ResourcePresetAdapter, ResourcePresetNode]:
        return ReadingTheId()

    @override
    def then(self) -> Then[APresetAndACaller, ResourcePresetNode]:
        return ThePresetNode()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadAPreset(
    Scenario[TestSeedingSession, APresetAndACaller, ResourcePresetAdapter, ResourcePresetNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-a-preset"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 id 로 프리셋을 읽으려 하면 권한 부족으로 거부됩니다",
            english=(
                "a user granted nothing reading a preset by id is rejected for not enough "
                "permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone()

    @override
    def when(self) -> When[APresetAndACaller, ResourcePresetAdapter, ResourcePresetNode]:
        return ReadingTheId()

    @override
    def then(self) -> Then[APresetAndACaller, ResourcePresetNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserReadingPresetsReadsSeveralIds(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, ResourcePresetAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-user-reading-presets-reads-several-presets-by-id"

    @override
    def describe(self) -> str:
        return Says(
            "public 에서 프리셋을 읽을 수 있는 사용자가 프리셋 여럿을 id 로 한 번에 읽으면, "
            "요청한 순서대로 프리셋이 옵니다",
            english=(
                "when a user who can read presets in public batch loads several presets by id, "
                "every preset comes back in the order requested"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(granted=Permission.READ)

    @override
    def when(self) -> When[ManyPresetsAndACaller, ResourcePresetAdapter, Loaded]:
        return ReadingSeveralIds()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Loaded]:
        return ThePresetsInTheOrderAsked()


@dataclass(frozen=True)
class AUserGrantedNothingIsRefusedPerId(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, ResourcePresetAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-batch-loading-presets-is-refused-per-item"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 id 여럿으로 프리셋을 읽으면, 호출은 거부되지 않고 "
            "물은 자리마다 권한 부족 거부가 옵니다",
            english=(
                "a user granted nothing batch loading presets by id is not rejected as a call, "
                "and every item asked carries a denial for not enough permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone()

    @override
    def when(self) -> When[ManyPresetsAndACaller, ResourcePresetAdapter, Loaded]:
        return ReadingSeveralIds()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Loaded]:
        return EveryItemIsRefused()


SCENARIOS: list[ReadingStep | LoadingStep] = [
    AUserGrantedReadReadsAPreset(),
    AUserGrantedNothingMayNotReadAPreset(),
    AUserReadingPresetsReadsSeveralIds(),
    AUserGrantedNothingIsRefusedPerId(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadingStep | LoadingStep,
    adapter: ResourcePresetAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
