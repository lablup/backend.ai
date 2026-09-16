"""프리셋 생성 — 순위가 어떻게 매겨지고, 무엇이 중복되면 안 되며, 누가 생성할 수 있는가.

값 종류가 ``flag``인데 대상이 ``args``가 아닌 요청과 값 종류에 맞지 않는 기본값은 여기 없다.
생성 요청 타입에서 거부하므로 어댑터가 보장하는 동작이 아니다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, override

import pytest

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
    """미리 만들어 둔 변형에 프리셋 하나를 생성하고 응답 노드를 반환한다."""

    named: str = MADE
    target: PresetTargetSpec = field(default_factory=lambda: ENV_STR)
    ui_option: UIOption | None = None

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: AVariantAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.variant.name} 변형에 {self.named} 프리셋을 생성"

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
    """이미 프리셋이 있는 변형에 하나 더 생성한다. 이름을 생략하면 기존 이름을 사용한다."""

    named: str | None = MADE

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: APresetAndACaller) -> str:
        return (
            f"{laid.caller.username}이 {laid.variant.name} 변형에 "
            f"{self.named or laid.preset.name} 프리셋을 하나 더 생성"
        )

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
    """프리셋이 없는 변형에 다른 변형의 프리셋과 같은 이름으로 생성한다."""

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: TwoVariantsAndAPreset) -> str:
        return f"{laid.caller.username}이 {laid.other.name} 변형에 {laid.preset.name} 프리셋을 생성"

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
    """같은 변형에 새로 생성한 프리셋. 순위는 기존 프리셋보다 지정된 간격만큼 크다."""

    started: datetime

    @override
    def says(self) -> str:
        return "순위가 기존 프리셋보다 지정된 간격만큼 큰 프리셋 전체가 반환된다"

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
            "프리셋이 없는 변형에 슈퍼관리자가 필수 항목만 지정해 생성하면 순위는 100이고, "
            "필수 항목으로 지정되지 않으며, 나머지 선택 항목은 비어 있다"
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
        return (
            "프리셋이 하나 있는 변형에 슈퍼관리자가 하나 더 생성하면 새 프리셋의 순위가 100 더 크다"
        )

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
        return "대상·값 종류·기본값·키를 모두 지정해 생성하면 네 값이 하나의 명세로 묶여 반환된다"

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
        return f"값 종류를 {self.target.value_type.value} 값으로 설정하고 올바른 기본값을 지정하면 생성된다"

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
        return "슬라이더 옵션을 추가하여 생성하면 UI 종류를 옵션에서 읽어 응답 노드에 함께 담는다"

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
        return "같은 변형에 같은 이름의 프리셋을 다시 생성하면 이름이 중복되어 요청이 거부된다"

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
        return "고유성 제약은 변형과 이름의 조합에 적용되므로 다른 변형에는 같은 이름의 프리셋을 생성할 수 있다"

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
        return "슈퍼관리자가 아닌 사용자가 프리셋을 생성하면 역할이 부족하여 요청이 거부된다"

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
            "권한 검사를 꺼도 슈퍼관리자가 아니면 프리셋을 생성할 수 없다. "
            "생성은 권한 그래프가 아니라 역할로 보호되므로 이 설정의 영향을 받지 않는다"
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
