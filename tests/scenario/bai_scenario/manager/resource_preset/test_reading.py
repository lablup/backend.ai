"""리소스 프리셋 읽기 — 하나씩, 그리고 id 여럿을 한 번에."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.resource_preset import ResourcePresetID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.resource_preset.response import ResourcePresetNode
from ai.backend.manager.api.adapters.resource_preset.adapter import ResourcePresetAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.resource import ResourcePresetNotFound
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
    """미리 만들어 둔 프리셋을 id 로 읽는다. ``unknown``이면 어느 행에도 없는 id 를 쓴다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: APresetAndACaller) -> str:
        target_ko = "없는 id" if self.unknown else laid.preset.name
        target_en = "an unknown id" if self.unknown else laid.preset.name
        return Says(
            f"{laid.caller.username}이 {target_ko}의 프리셋을 읽습니다",
            english=f"{laid.caller.username} reads the preset of {target_en}",
        )

    @override
    async def call(
        self, adapter: ResourcePresetAdapter, laid: APresetAndACaller
    ) -> ResourcePresetNode:
        target = uuid4() if self.unknown else laid.preset.id
        with ActingAs(laid.caller):
            return await adapter.get(target)


@dataclass(frozen=True)
class ReadingSeveralIds(When[ManyPresetsAndACaller, ResourcePresetAdapter, Loaded]):
    """미리 만들어 둔 프리셋들의 id 와 없는 id 하나로 여럿을 읽는다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 프리셋 {len(laid.laid)}개와 없는 id 하나를 한 번에 읽습니다",
            english=(
                f"{laid.caller.username} reads {len(laid.laid)} presets and one unknown id at once"
            ),
        )

    @override
    async def call(self, adapter: ResourcePresetAdapter, laid: ManyPresetsAndACaller) -> Loaded:
        ids = [ResourcePresetID(one.id) for one in laid.laid]
        ids.append(ResourcePresetID(uuid4()))
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids(ids)


@dataclass(frozen=True)
class ThePresetsInTheOrderAsked(Then[ManyPresetsAndACaller, Loaded]):
    """요청한 순서대로 프리셋 전체가 오고, 없는 id 의 자리는 비어 있다."""

    @override
    def says(self) -> str:
        return Says(
            "요청한 순서대로 프리셋 전체가 오고, 없는 id 의 자리는 비어 있습니다",
            english=(
                "every preset comes back in the order requested, and the item for the unknown "
                "id is empty"
            ),
        )

    @override
    def look(self, laid: ManyPresetsAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [MissingResponse(answered.raised)]
        if len(items) != len(laid.laid) + 1:
            return [Same("len(items)", len(items), len(laid.laid) + 1)]
        seen: list[Verdict] = [Same("len(items)", len(items), len(laid.laid) + 1)]
        for i, preset in enumerate(laid.laid):
            node = items[i]
            if not isinstance(node, ResourcePresetNode):
                seen.append(Same(f"items[{i}]", type(node).__name__, Says("노드", english="node")))
                continue
            seen += preset_verdicts(f"items[{i}].", node, preset)
        seen.append(Same(f"items[{len(laid.laid)}]", items[len(laid.laid)], None))
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
        seen: list[Verdict] = [Same("len(items)", len(items), len(laid.laid) + 1)]
        for i in range(len(laid.laid) + 1):
            got = items[i] if i < len(items) else None
            seen.append(
                Refused(NotEnoughPermission, got if isinstance(got, BaseException) else None)
            )
        return seen


@dataclass(frozen=True)
class TheSuperadminReadsAPreset(
    Scenario[TestSeedingSession, APresetAndACaller, ResourcePresetAdapter, ResourcePresetNode]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-reads-a-preset-by-id"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 id 로 프리셋 하나를 읽으면, 미리 저장한 프리셋 전체가 반환됩니다",
            english=(
                "when the superadmin reads one preset by id, the whole preset seeded in advance "
                "comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APresetAndACaller, ResourcePresetAdapter, ResourcePresetNode]:
        return ReadingTheId()

    @override
    def then(self) -> Then[APresetAndACaller, ResourcePresetNode]:
        return ThePresetNode()


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
class AnIdNothingAnswersToIsNotFound(
    Scenario[TestSeedingSession, APresetAndACaller, ResourcePresetAdapter, ResourcePresetNode]
):
    @override
    def summary(self) -> str:
        return "reading-an-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 없는 id 의 프리셋을 읽으려 하면 대상이 없다는 것으로 거부됩니다",
            english=(
                "when the superadmin reads the preset of an unknown id, the call is rejected as "
                "no such target"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APresetAndACaller, ResourcePresetAdapter, ResourcePresetNode]:
        return ReadingTheId(unknown=True)

    @override
    def then(self) -> Then[APresetAndACaller, ResourcePresetNode]:
        return TheCallIsRefused(ResourcePresetNotFound)


@dataclass(frozen=True)
class TheSuperadminReadsSeveralIds(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, ResourcePresetAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-reads-several-presets-by-id"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 프리셋 여럿과 없는 id 하나를 한 번에 읽으면, 요청한 순서대로 "
            "프리셋이 오고 없는 id 의 자리는 비어 있습니다",
            english=(
                "when the superadmin batch loads several presets and one unknown id, every "
                "preset comes back in the order requested and the item for the unknown id is "
                "empty"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(role=UserRole.SUPERADMIN)

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
    TheSuperadminReadsAPreset(),
    AUserGrantedReadReadsAPreset(),
    AUserGrantedNothingMayNotReadAPreset(),
    AnIdNothingAnswersToIsNotFound(),
    TheSuperadminReadsSeveralIds(),
    AUserGrantedNothingIsRefusedPerId(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadingStep | LoadingStep,
    adapter: ResourcePresetAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
