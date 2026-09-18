"""What a runtime variant preset scenario table says besides the call.

A preset is laid under a variant and created in no scope. A table needs the caller, the
variant a preset would go under, and the preset or presets the call reads.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.runtime_variant_preset.response import (
    DeleteRuntimeVariantPresetPayload,
    PresetTargetSpec,
    RuntimeVariantPresetNode,
    SearchRuntimeVariantPresetsPayload,
)
from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import (
    PresetTarget,
    PresetValueType,
    UIOption,
)
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Skipped,
    Then,
    Verdict,
)
from bai_scenario.components.domain import WrittenByThisRun
from bai_scenario.components.runtime_variant import AVariantAndACaller
from bai_scenario.components.system import KEPT, Kept, lay_a_caller, role_named
from bai_scenario.seeds.runtime_variant.preset import SeedRuntimeVariantPreset
from bai_scenario.seeds.runtime_variant.runtime_variant import SeedRuntimeVariant

DESCRIBED = "미리 만들어 둔 프리셋"
"""시드가 미리 만들어 두는 프리셋의 설명. 시나리오가 기대값으로 다시 쓰므로 한 곳에 둔다."""

KEY = "PRESET_KEY"
"""시드가 미리 만들어 두는 프리셋의 키."""

RANK_GAP = 100
"""생성 시 같은 변형에서 가장 큰 순위에 더하는 값. 첫 프리셋의 순위이기도 하다."""


@dataclass(frozen=True)
class APresetAndACaller:
    """프리셋 하나와 해당 변형, 그리고 호출할 사용자."""

    variant: RuntimeVariantData
    preset: RuntimeVariantPresetData
    caller: UserData


@dataclass(frozen=True)
class TwoVariantsAndAPreset:
    """변형 둘과 한쪽에만 있는 프리셋 하나, 그리고 호출할 사용자."""

    variant: RuntimeVariantData
    other: RuntimeVariantData
    preset: RuntimeVariantPresetData
    caller: UserData


@dataclass(frozen=True)
class ManyPresetsAndACaller:
    """검색 대상 프리셋과 호출할 사용자. ``laid``에는 응답에 포함할 프리셋만 담는다."""

    variant: RuntimeVariantData
    laid: tuple[RuntimeVariantPresetData, ...]
    caller: UserData


@dataclass(frozen=True)
class APresetAndSomeone(Given[Any, APresetAndACaller]):
    """변형 하나, 해당 변형의 프리셋 하나, 사용자 한 명."""

    role: UserRole = UserRole.USER
    preset_target: PresetTarget = PresetTarget.ENV
    value_type: PresetValueType = PresetValueType.STR
    default_value: str | None = None

    @override
    def describe(self) -> str:
        return f"변형 하나와 해당 변형의 프리셋 하나, 그리고 {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> APresetAndACaller:
        variant = await seeding.creating(SeedRuntimeVariant())
        preset = await seeding.creating_from(
            SeedRuntimeVariantPreset(
                preset_target=self.preset_target,
                value_type=self.value_type,
                default_value=self.default_value,
            ),
            variant,
        )
        caller = await lay_a_caller(seeding, self.role)
        return APresetAndACaller(seeding.made(variant), seeding.made(preset), seeding.made(caller))


@dataclass(frozen=True)
class TwoVariantsOneWithAPreset(Given[Any, TwoVariantsAndAPreset]):
    """변형 둘, 한쪽에만 있는 프리셋 하나, 사용자 한 명."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"변형 둘과 한쪽에만 있는 프리셋 하나, 그리고 {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> TwoVariantsAndAPreset:
        variant = await seeding.creating(SeedRuntimeVariant(name_hint="taken"))
        other = await seeding.creating(SeedRuntimeVariant(name_hint="free"))
        preset = await seeding.creating_from(SeedRuntimeVariantPreset(), variant)
        caller = await lay_a_caller(seeding, self.role)
        return TwoVariantsAndAPreset(
            seeding.made(variant), seeding.made(other), seeding.made(preset), seeding.made(caller)
        )


@dataclass(frozen=True)
class ManyPresetsAndSomeone(Given[Any, ManyPresetsAndACaller]):
    """한 변형의 프리셋 여러 개와 사용자 한 명."""

    role: UserRole = UserRole.USER
    besides: int = 1

    @override
    def describe(self) -> str:
        return f"한 변형의 프리셋 {self.besides + 1}개와 {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> ManyPresetsAndACaller:
        variant = await seeding.creating(SeedRuntimeVariant())
        presets = [
            await seeding.creating_from(SeedRuntimeVariantPreset(), variant)
            for _ in range(self.besides + 1)
        ]
        caller = await lay_a_caller(seeding, self.role)
        return ManyPresetsAndACaller(
            variant=seeding.made(variant),
            laid=tuple(seeding.made(one) for one in presets),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class PresetsInTwoVariants(Given[Any, ManyPresetsAndACaller]):
    """두 변형에 나뉘어 있는 프리셋과 사용자 한 명. ``laid``에는 첫 변형의 것만 담는다."""

    @override
    def describe(self) -> str:
        return "두 변형에 나뉘어 있는 프리셋 세 개와 일반 사용자 한 명"

    @override
    async def lay(self, seeding: Any) -> ManyPresetsAndACaller:
        variant = await seeding.creating(SeedRuntimeVariant(name_hint="wanted"))
        other = await seeding.creating(SeedRuntimeVariant(name_hint="other"))
        mine = [
            await seeding.creating_from(SeedRuntimeVariantPreset(name_hint="mine"), variant)
            for _ in range(2)
        ]
        await seeding.creating_from(SeedRuntimeVariantPreset(name_hint="elsewhere"), other)
        caller = await lay_a_caller(seeding)
        return ManyPresetsAndACaller(
            variant=seeding.made(variant),
            laid=tuple(seeding.made(one) for one in mine),
            caller=seeding.made(caller),
        )


VALID_AT = "2.5.0"
"""버전 필터로 지정하는 버전. 아래 다섯 중 둘만 이 버전에 유효하다."""


@dataclass(frozen=True)
class PresetsAcrossVersions(Given[Any, ManyPresetsAndACaller]):
    """추가·폐기 버전이 서로 다른 프리셋 다섯 개. ``laid``에는 지정한 버전에 유효한 것만 담는다."""

    @override
    def describe(self) -> str:
        return "추가 버전과 폐기 버전이 서로 다른 프리셋 다섯 개와 일반 사용자 한 명"

    @override
    async def lay(self, seeding: Any) -> ManyPresetsAndACaller:
        variant = await seeding.creating(SeedRuntimeVariant())
        valid = [
            await seeding.creating_from(
                SeedRuntimeVariantPreset(name_hint="open", added_version="1.0.0"), variant
            ),
            await seeding.creating_from(SeedRuntimeVariantPreset(name_hint="unbounded"), variant),
        ]
        await seeding.creating_from(
            SeedRuntimeVariantPreset(
                name_hint="closed", added_version="1.0.0", deprecated_version="2.0.0"
            ),
            variant,
        )
        await seeding.creating_from(
            SeedRuntimeVariantPreset(name_hint="retired", deprecated_version="2.0.0"), variant
        )
        await seeding.creating_from(
            SeedRuntimeVariantPreset(name_hint="upcoming", added_version="3.0.0"), variant
        )
        caller = await lay_a_caller(seeding)
        return ManyPresetsAndACaller(
            variant=seeding.made(variant),
            laid=tuple(seeding.made(one) for one in valid),
            caller=seeding.made(caller),
        )


def preset_verdicts(
    at: str,
    node: RuntimeVariantPresetNode,
    *,
    variant_id: UUID,
    named: str,
    described: str | None,
    rank: int,
    target: PresetTargetSpec,
    required: bool,
    added: str | None,
    deprecated: str | None,
    category: str | None,
    display_name: str | None,
    ui_option: UIOption | None,
    written: WrittenByThisRun,
) -> list[Verdict]:
    """Every place of one preset node, prefixed for a node inside a list."""
    return [
        Skipped(f"{at}id", "데이터베이스가 만든다"),
        Held(
            f"{at}runtime_variant_id",
            node.runtime_variant_id,
            SameAs(variant_id, "미리 만들어 둔 변형의 식별자"),
        ),
        Same(f"{at}name", node.name, named),
        Same(f"{at}description", node.description, described),
        Same(f"{at}rank", node.rank, rank),
        Same(f"{at}target_spec", node.target_spec, target),
        Same(f"{at}required", node.required, required),
        Same(f"{at}added_version", node.added_version, added),
        Same(f"{at}deprecated_version", node.deprecated_version, deprecated),
        Same(f"{at}category", node.category, category),
        Same(f"{at}ui_type", node.ui_type, ui_option.ui_type.value if ui_option else None),
        Same(f"{at}display_name", node.display_name, display_name),
        Same(f"{at}ui_option", node.ui_option, ui_option),
        Held(f"{at}created_at", node.created_at, written),
        Held(f"{at}updated_at", node.updated_at, written),
    ]


def laid_preset_verdicts(
    at: str,
    node: RuntimeVariantPresetNode,
    laid: RuntimeVariantPresetData,
    written: WrittenByThisRun,
) -> list[Verdict]:
    """Every place of one preset node, against the row the seed laid."""
    return preset_verdicts(
        at,
        node,
        variant_id=laid.runtime_variant_id,
        named=laid.name,
        described=laid.description,
        rank=laid.rank,
        target=PresetTargetSpec(
            preset_target=laid.preset_target,
            value_type=laid.value_type,
            default_value=laid.default_value,
            key=laid.key,
        ),
        required=laid.required,
        added=laid.added_version,
        deprecated=laid.deprecated_version,
        category=laid.category,
        display_name=laid.display_name,
        ui_option=None,
        written=written,
    )


@dataclass(frozen=True)
class TheNewPresetNode(Then[AVariantAndACaller, RuntimeVariantPresetNode]):
    """방금 생성한 프리셋 전체가 반환된다. 기대값은 요청과 미리 만들어 둔 변형에서 읽는다."""

    started: datetime
    named: str
    target: PresetTargetSpec
    rank: int = RANK_GAP
    described: str | None = None
    required: bool = False
    added: str | None = None
    deprecated: str | None = None
    category: str | None = None
    display_name: str | None = None
    ui_option: UIOption | None = None

    @override
    def says(self) -> str:
        return "생성한 프리셋 전체가 반환된다"

    @override
    def look(
        self, laid: AVariantAndACaller, answered: Answered[RuntimeVariantPresetNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return preset_verdicts(
            "",
            node,
            variant_id=laid.variant.id,
            named=self.named,
            described=self.described,
            rank=self.rank,
            target=self.target,
            required=self.required,
            added=self.added,
            deprecated=self.deprecated,
            category=self.category,
            display_name=self.display_name,
            ui_option=self.ui_option,
            written=WrittenByThisRun(self.started),
        )


@dataclass(frozen=True)
class TheSameNameUnderTheOtherVariant(Then[TwoVariantsAndAPreset, RuntimeVariantPresetNode]):
    """다른 변형에 같은 이름으로 생성한 프리셋 전체가 반환된다."""

    started: datetime
    target: PresetTargetSpec

    @override
    def says(self) -> str:
        return "다른 변형에 생성한 프리셋 전체가 반환된다"

    @override
    def look(
        self, laid: TwoVariantsAndAPreset, answered: Answered[RuntimeVariantPresetNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return preset_verdicts(
            "",
            node,
            variant_id=laid.other.id,
            named=laid.preset.name,
            described=None,
            rank=RANK_GAP,
            target=self.target,
            required=False,
            added=None,
            deprecated=None,
            category=None,
            display_name=None,
            ui_option=None,
            written=WrittenByThisRun(self.started),
        )


@dataclass(frozen=True)
class ThePresetNode(Then[APresetAndACaller, RuntimeVariantPresetNode]):
    """미리 만들어 둔 프리셋 전체가 반환된다. 수정 요청에는 변경할 필드만 담는다."""

    started: datetime
    named: str | Kept = KEPT
    described: str | None | Kept = KEPT
    rank: int | Kept = KEPT

    @override
    def says(self) -> str:
        return "미리 만들어 둔 프리셋 전체가 반환된다"

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
            named=laid.preset.name if isinstance(self.named, Kept) else self.named,
            described=(
                laid.preset.description if isinstance(self.described, Kept) else self.described
            ),
            rank=laid.preset.rank if isinstance(self.rank, Kept) else self.rank,
            target=PresetTargetSpec(
                preset_target=laid.preset.preset_target,
                value_type=laid.preset.value_type,
                default_value=laid.preset.default_value,
                key=laid.preset.key,
            ),
            required=laid.preset.required,
            added=laid.preset.added_version,
            deprecated=laid.preset.deprecated_version,
            category=laid.preset.category,
            display_name=laid.preset.display_name,
            ui_option=None,
            written=WrittenByThisRun(self.started),
        )


@dataclass(frozen=True)
class TheLaidPresetsAreLeft(Then[ManyPresetsAndACaller, SearchRuntimeVariantPresetsPayload]):
    """응답에 포함되어야 하는 프리셋만 반환된다."""

    @override
    def says(self) -> str:
        return "응답에 포함되어야 하는 프리셋만 반환된다"

    @override
    def look(
        self, laid: ManyPresetsAndACaller, answered: Answered[SearchRuntimeVariantPresetsPayload]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Same(
                "items",
                sorted(one.name for one in page.items),
                sorted(one.name for one in laid.laid),
            ),
            Same("total_count", page.total_count, len(laid.laid)),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheFirstPageOfPresets(Then[ManyPresetsAndACaller, SearchRuntimeVariantPresetsPayload]):
    """페이지 크기를 생략한 첫 페이지. 기본 크기만큼 반환하고 다음 페이지가 있음을 표시한다."""

    size: int

    @override
    def says(self) -> str:
        return "기본 크기의 첫 페이지가 반환된다"

    @override
    def look(
        self, laid: ManyPresetsAndACaller, answered: Answered[SearchRuntimeVariantPresetsPayload]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Same("len(items)", len(page.items), self.size),
            Same("total_count", page.total_count, len(laid.laid)),
            Same("has_next_page", page.has_next_page, True),
            Same("has_previous_page", page.has_previous_page, False),
        ]


@dataclass(frozen=True)
class ThePresetsInTheOrderAsked(Then[ManyPresetsAndACaller, list[RuntimeVariantPresetNode | None]]):
    """요청한 순서대로 반환한다. 존재하지 않는 ID의 위치에는 빈 항목을 반환한다."""

    started: datetime

    @override
    def says(self) -> str:
        return "요청한 순서대로 반환되며, 존재하지 않는 ID의 위치에는 빈 항목이 반환된다"

    @override
    def look(
        self,
        laid: ManyPresetsAndACaller,
        answered: Answered[list[RuntimeVariantPresetNode | None]],
    ) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        written = WrittenByThisRun(self.started)
        asked = len(laid.laid) + 1
        seen: list[Verdict] = [Same("len(items)", len(items), asked)]
        for i, expected in enumerate(laid.laid):
            got = items[i] if i < len(items) else None
            if got is None:
                seen.append(Same(f"items[{i}]", got, "노드"))
                continue
            seen.extend(laid_preset_verdicts(f"items[{i}].", got, expected, written))
        last = items[asked - 1] if len(items) >= asked else "없음"
        seen.append(Same(f"items[{asked - 1}]", last, None))
        return seen


@dataclass(frozen=True)
class TheDeletedPresetId(Then[APresetAndACaller, DeleteRuntimeVariantPresetPayload]):
    """삭제한 프리셋의 ID를 담은 응답."""

    @override
    def says(self) -> str:
        return "삭제한 프리셋의 ID가 반환된다"

    @override
    def look(
        self, laid: APresetAndACaller, answered: Answered[DeleteRuntimeVariantPresetPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Held[UUID](
                "id", payload.id, SameAs[UUID](laid.preset.id, "미리 만들어 둔 프리셋의 식별자")
            )
        ]
