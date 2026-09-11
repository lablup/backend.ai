"""preset 만들기 — 순위가 어떻게 매겨지고, 무엇이 겹치면 안 되며, 누가 만들 수 있는가.

flag를 args 아닌 대상에 두는 요청과 값 종류에 맞지 않는 기본값은 여기 없다. 만들 때는 요청
타입이 막으므로 어댑터가 보장하는 것이 아니다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.domain import WrittenByThisRun
from bai_scenario.components.runtime_variant import AVariantAndACaller, AVariantAndSomeone
from bai_scenario.components.runtime_variant_preset import (
    RANK_GAP,
    APresetAndACaller,
    APresetAndSomeone,
    TheNewPresetNode,
    TheSameNameUnderTheOtherVariant,
    TwoVariantsAndAPreset,
    TwoVariantsOneWithAPreset,
    preset_verdicts,
)
from bai_scenario.components.system import ENFORCEMENT
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.runtime_variant_preset.request import (
    CreateRuntimeVariantPresetInput,
)
from ai.backend.common.dto.manager.v2.runtime_variant_preset.response import (
    PresetTargetSpec,
    RuntimeVariantPresetNode,
)
from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import (
    PresetTarget,
    PresetValueType,
    SliderOption,
    UIOption,
    UIType,
)
from ai.backend.manager.api.adapters.runtime_variant_preset.adapter import (
    RuntimeVariantPresetAdapter,
)
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.resource import RuntimeVariantPresetConflict
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Configured,
    Given,
    Refused,
    Scenario,
    Then,
    Verdict,
    When,
)

MADE = "max-tokens"
KEY = "MAX_TOKENS"
ENV_STR = PresetTargetSpec(
    preset_target=PresetTarget.ENV, value_type=PresetValueType.STR, default_value=None, key=KEY
)
ARGS_INT = PresetTargetSpec(
    preset_target=PresetTarget.ARGS,
    value_type=PresetValueType.INT,
    default_value="4",
    key="--workers",
)
SLIDER = UIOption(ui_type=UIType.SLIDER, slider=SliderOption(min=1, max=8, step=1))

type CreatingStep = Scenario[
    SeedingSession, Any, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode
]


@dataclass(frozen=True)
class Creating(When[AVariantAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode]):
    """심은 변형 아래 preset 하나를 만든다. 답이 실은 노드를 벗겨서 준다."""

    named: str = MADE
    target: PresetTargetSpec = field(default_factory=lambda: ENV_STR)
    ui_option: UIOption | None = None

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: AVariantAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.variant.name}에 {self.named} preset을 만듦"

    @override
    async def call(
        self, adapter: RuntimeVariantPresetAdapter, laid: AVariantAndACaller
    ) -> RuntimeVariantPresetNode:
        with ActingAs(laid.caller):
            payload = await adapter.create(
                CreateRuntimeVariantPresetInput(
                    runtime_variant_id=laid.variant.id,
                    name=self.named,
                    preset_target=self.target.preset_target,
                    value_type=self.target.value_type,
                    default_value=self.target.default_value,
                    key=self.target.key,
                    ui_option=self.ui_option,
                )
            )
        return payload.preset


@dataclass(frozen=True)
class CreatingBesideTheLaidOne(
    When[APresetAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode]
):
    """이미 preset이 하나 있는 변형에 하나 더 만든다. 이름을 대지 않으면 심은 것과 같은 이름을 쓴다."""

    named: str | None = MADE

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: APresetAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.variant.name}에 {self.named or laid.preset.name} preset을 하나 더 만듦"

    @override
    async def call(
        self, adapter: RuntimeVariantPresetAdapter, laid: APresetAndACaller
    ) -> RuntimeVariantPresetNode:
        with ActingAs(laid.caller):
            payload = await adapter.create(
                CreateRuntimeVariantPresetInput(
                    runtime_variant_id=laid.variant.id,
                    name=self.named or laid.preset.name,
                    preset_target=ENV_STR.preset_target,
                    value_type=ENV_STR.value_type,
                    key=ENV_STR.key,
                )
            )
        return payload.preset


@dataclass(frozen=True)
class CreatingTheSameNameUnderTheOther(
    When[TwoVariantsAndAPreset, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode]
):
    """preset이 없는 쪽 변형에, 있는 쪽 preset과 같은 이름으로 만든다."""

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: TwoVariantsAndAPreset) -> str:
        return f"{laid.caller.username}이 {laid.other.name}에 {laid.preset.name} preset을 만듦"

    @override
    async def call(
        self, adapter: RuntimeVariantPresetAdapter, laid: TwoVariantsAndAPreset
    ) -> RuntimeVariantPresetNode:
        with ActingAs(laid.caller):
            payload = await adapter.create(
                CreateRuntimeVariantPresetInput(
                    runtime_variant_id=laid.other.id,
                    name=laid.preset.name,
                    preset_target=ENV_STR.preset_target,
                    value_type=ENV_STR.value_type,
                    key=ENV_STR.key,
                )
            )
        return payload.preset


@dataclass(frozen=True)
class TheNextPresetNode(Then[APresetAndACaller, RuntimeVariantPresetNode]):
    """같은 변형에 하나 더 만든 preset. 순위가 앞의 것보다 간격만큼 크다."""

    started: datetime

    @override
    def says(self) -> str:
        return "순위가 앞의 것보다 간격만큼 큰 preset 전체가 온다"

    @override
    def look(
        self, laid: APresetAndACaller, answered: Answered[RuntimeVariantPresetNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return preset_verdicts(
            "",
            node,
            variant_id=laid.variant.id,
            named=MADE,
            described=None,
            rank=laid.preset.rank + RANK_GAP,
            target=ENV_STR,
            required=False,
            added=None,
            deprecated=None,
            category=None,
            display_name=None,
            ui_option=None,
            written=WrittenByThisRun(self.started),
        )


@dataclass(frozen=True)
class TheFirstPresetIsRankedAHundred(
    Scenario[
        SeedingSession, AVariantAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode
    ]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-first-preset-of-a-variant-is-ranked-a-hundred"

    @override
    def describe(self) -> str:
        return (
            "preset이 없는 변형에 슈퍼관리자가 필수 항목만 주고 만들면, 순위는 백, 필수 여부는 거짓, "
            "나머지 선택 항목은 빈 노드가 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, AVariantAndACaller]:
        return AVariantAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[AVariantAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode]:
        return Creating()

    @override
    def then(self) -> Then[AVariantAndACaller, RuntimeVariantPresetNode]:
        return TheNewPresetNode(started=self.started, named=MADE, target=ENV_STR)


@dataclass(frozen=True)
class TheSecondPresetIsRankedAHundredHigher(
    Scenario[
        SeedingSession, APresetAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode
    ]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-second-preset-in-the-same-variant-is-ranked-a-hundred-higher"

    @override
    def describe(self) -> str:
        return "preset이 하나 있는 변형에 슈퍼관리자가 하나 더 만들면 순위가 앞의 것보다 백 크다"

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[APresetAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode]:
        return CreatingBesideTheLaidOne()

    @override
    def then(self) -> Then[APresetAndACaller, RuntimeVariantPresetNode]:
        return TheNextPresetNode(started=self.started)


@dataclass(frozen=True)
class FourValuesComeBackAsOneSpec(
    Scenario[
        SeedingSession, AVariantAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode
    ]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "target-value-type-default-and-key-come-back-as-one-spec"

    @override
    def describe(self) -> str:
        return "대상·값 종류·기본값·키를 따로 주고 만들면, 답에서는 넷이 한 명세로 묶여 온다"

    @override
    def given(self) -> Given[SeedingSession, AVariantAndACaller]:
        return AVariantAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[AVariantAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode]:
        return Creating(target=ARGS_INT)

    @override
    def then(self) -> Then[AVariantAndACaller, RuntimeVariantPresetNode]:
        return TheNewPresetNode(started=self.started, named=MADE, target=ARGS_INT)


@dataclass(frozen=True)
class ADefaultValueOfEachType(
    Scenario[
        SeedingSession, AVariantAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode
    ]
):
    started: datetime
    target: PresetTargetSpec

    @override
    def summary(self) -> str:
        return f"a-{self.target.value_type.value}-default-value-that-fits-its-type-is-accepted"

    @override
    def describe(self) -> str:
        return f"값 종류를 {self.target.value_type.value}로 두고 그에 맞는 기본값을 주면 만들어진다"

    @override
    def given(self) -> Given[SeedingSession, AVariantAndACaller]:
        return AVariantAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[AVariantAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode]:
        return Creating(target=self.target)

    @override
    def then(self) -> Then[AVariantAndACaller, RuntimeVariantPresetNode]:
        return TheNewPresetNode(started=self.started, named=MADE, target=self.target)


@dataclass(frozen=True)
class AUiOptionCarriesItsType(
    Scenario[
        SeedingSession, AVariantAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode
    ]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-ui-option-given-on-create-carries-its-type-into-the-node"

    @override
    def describe(self) -> str:
        return "슬라이더 옵션을 붙여 만들면, UI 종류가 옵션에서 읽혀 노드에 함께 실린다"

    @override
    def given(self) -> Given[SeedingSession, AVariantAndACaller]:
        return AVariantAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[AVariantAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode]:
        return Creating(ui_option=SLIDER)

    @override
    def then(self) -> Then[AVariantAndACaller, RuntimeVariantPresetNode]:
        return TheNewPresetNode(started=self.started, named=MADE, target=ENV_STR, ui_option=SLIDER)


@dataclass(frozen=True)
class ANameTakenInTheSameVariantIsRefused(
    Scenario[
        SeedingSession, APresetAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode
    ]
):
    @override
    def summary(self) -> str:
        return "a-preset-name-taken-in-the-same-variant-is-refused"

    @override
    def describe(self) -> str:
        return (
            "같은 변형에 같은 이름의 preset이 있을 때 다시 만들면, 이름이 겹친다는 이유로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[APresetAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode]:
        return CreatingBesideTheLaidOne(named=None)

    @override
    def then(self) -> Then[APresetAndACaller, RuntimeVariantPresetNode]:
        return TheCallIsRefused(RuntimeVariantPresetConflict)


@dataclass(frozen=True)
class TheSameNameIsFreeInAnotherVariant(
    Scenario[
        SeedingSession, TwoVariantsAndAPreset, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode
    ]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-same-preset-name-is-free-in-another-variant"

    @override
    def describe(self) -> str:
        return "유니크 제약이 변형과 이름의 짝에 걸려 있으므로, 다른 변형에는 같은 이름의 preset을 만들 수 있다"

    @override
    def given(self) -> Given[SeedingSession, TwoVariantsAndAPreset]:
        return TwoVariantsOneWithAPreset(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[TwoVariantsAndAPreset, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode]:
        return CreatingTheSameNameUnderTheOther()

    @override
    def then(self) -> Then[TwoVariantsAndAPreset, RuntimeVariantPresetNode]:
        return TheSameNameUnderTheOtherVariant(started=self.started, target=ENV_STR)


@dataclass(frozen=True)
class AUserWhoIsNotTheSuperadminMayNotCreate(
    Scenario[
        SeedingSession, AVariantAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-create-a-preset"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아닌 사용자가 preset을 만들면 역할로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AVariantAndACaller]:
        return AVariantAndSomeone()

    @override
    def when(
        self,
    ) -> When[AVariantAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode]:
        return Creating()

    @override
    def then(self) -> Then[AVariantAndACaller, RuntimeVariantPresetNode]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class EnforcementOffStillNeedsTheSuperadmin(
    Scenario[
        SeedingSession, AVariantAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode
    ],
    Configured,
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-does-not-let-a-user-create-a-preset"

    @override
    def describe(self) -> str:
        return (
            "엔티티 권한 집행을 꺼도 슈퍼관리자가 아니면 preset을 만들지 못한다. "
            "이 문은 권한 그래프가 아니라 역할이라 스위치와 무관하다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, AVariantAndACaller]:
        return AVariantAndSomeone()

    @override
    def when(
        self,
    ) -> When[AVariantAndACaller, RuntimeVariantPresetAdapter, RuntimeVariantPresetNode]:
        return Creating()

    @override
    def then(self) -> Then[AVariantAndACaller, RuntimeVariantPresetNode]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[CreatingStep] = [
    TheFirstPresetIsRankedAHundred(started=datetime.now(UTC)),
    TheSecondPresetIsRankedAHundredHigher(started=datetime.now(UTC)),
    FourValuesComeBackAsOneSpec(started=datetime.now(UTC)),
    ADefaultValueOfEachType(
        started=datetime.now(UTC),
        target=PresetTargetSpec(
            preset_target=PresetTarget.ENV,
            value_type=PresetValueType.STR,
            default_value="abc",
            key=KEY,
        ),
    ),
    ADefaultValueOfEachType(
        started=datetime.now(UTC),
        target=PresetTargetSpec(
            preset_target=PresetTarget.ENV,
            value_type=PresetValueType.INT,
            default_value="4",
            key=KEY,
        ),
    ),
    ADefaultValueOfEachType(
        started=datetime.now(UTC),
        target=PresetTargetSpec(
            preset_target=PresetTarget.ENV,
            value_type=PresetValueType.FLOAT,
            default_value="0.5",
            key=KEY,
        ),
    ),
    ADefaultValueOfEachType(
        started=datetime.now(UTC),
        target=PresetTargetSpec(
            preset_target=PresetTarget.ENV,
            value_type=PresetValueType.BOOL,
            default_value="true",
            key=KEY,
        ),
    ),
    ADefaultValueOfEachType(
        started=datetime.now(UTC),
        target=PresetTargetSpec(
            preset_target=PresetTarget.ARGS,
            value_type=PresetValueType.FLAG,
            default_value="true",
            key=KEY,
        ),
    ),
    AUiOptionCarriesItsType(started=datetime.now(UTC)),
    ANameTakenInTheSameVariantIsRefused(),
    TheSameNameIsFreeInAnotherVariant(started=datetime.now(UTC)),
    AUserWhoIsNotTheSuperadminMayNotCreate(),
    EnforcementOffStillNeedsTheSuperadmin(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: CreatingStep, adapter: RuntimeVariantPresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
