"""프리셋 수정 — 누가 수정할 수 있고, 무엇이 템플릿과 카테고리를 막는가.

템플릿 검증은 요청이 템플릿을 지정한 때만 실행된다. 필터 라벨과 그룹 라벨은 한 컬럼에 같이
저장되지만 하나만 수정해도 다른 하나가 지워지지 않는다.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import UUID, uuid4

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.prometheus_query_preset import (
    APresetAndACaller,
    APresetAndSomeone,
    APresetInOneOfTwoCategories,
    PresetNodeAnswer,
    ThePresetNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.prometheus_query_preset.preset import UNRENDERABLE

from ai.backend.common.api_handlers import SENTINEL, Sentinel
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    ModifyQueryDefinitionInput,
    ModifyQueryDefinitionOptionsInput,
)
from ai.backend.common.exception import InvalidMetricPresetTemplate
from ai.backend.manager.api.adapters.prometheus_query_preset.adapter import (
    PrometheusQueryPresetAdapter,
)
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.repository import ForeignKeyViolationError
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Configured,
    Given,
    Scenario,
    Then,
    When,
)

RENAMED = "cpu-by-session"
RETUNED = "sum by (${{group_by}}) (rate(container_cpu_seconds_total{${{labels}}}[${{window}}]))"
ENFORCEMENT = "manager.rbac.enforcement_enabled"

type EditingStep = Scenario[
    SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer
]


@dataclass(frozen=True)
class Editing(When[APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]):
    """미리 만들어 둔 프리셋을 수정한다. 지정하지 않은 필드는 요청에서 빠진다."""

    named: str | None = None
    query_template: str | None = None
    clear_description: bool = False
    move_elsewhere: bool = False
    under_an_unknown_category: bool = False
    filter_labels: Sequence[str] | None = None
    other: UUID | None = None

    @override
    def operation(self) -> str:
        return "update"

    @override
    def describe(self, laid: APresetAndACaller) -> str:
        target = "존재하지 않는 id" if self.other is not None else laid.preset.name
        changed = [
            what
            for what, asked in (
                ("이름 변경", self.named is not None),
                ("템플릿 변경", self.query_template is not None),
                ("설명 비우기", self.clear_description),
                ("다른 카테고리로 이동", self.move_elsewhere),
                ("존재하지 않는 카테고리 id로 이동", self.under_an_unknown_category),
                ("필터 라벨 변경", self.filter_labels is not None),
            )
            if asked
        ]
        if not changed:
            return f"{laid.caller.username}이 {target} 수정 (빈 요청)"
        return f"{laid.caller.username}이 {target} 수정 ({', '.join(changed)})"

    def _category(self, laid: APresetAndACaller) -> UUID | Sentinel | None:
        if self.move_elsewhere and laid.elsewhere is not None:
            return laid.elsewhere.id
        if self.under_an_unknown_category:
            return uuid4()
        return SENTINEL

    @override
    async def call(
        self, adapter: PrometheusQueryPresetAdapter, laid: APresetAndACaller
    ) -> PresetNodeAnswer:
        wanted = self.other if self.other is not None else laid.preset.id
        with ActingAs(laid.caller):
            payload = await adapter.update(
                wanted,
                ModifyQueryDefinitionInput(
                    name=self.named,
                    query_template=self.query_template,
                    description=None if self.clear_description else SENTINEL,
                    category_id=self._category(laid),
                    options=(
                        ModifyQueryDefinitionOptionsInput(filter_labels=list(self.filter_labels))
                        if self.filter_labels is not None
                        else None
                    ),
                ),
            )
        return payload.item


@dataclass(frozen=True)
class TheSuperadminRetunesTheTemplate(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-changes-the-template-and-the-rest-stays"

    @override
    def describe(self) -> str:
        return "프리셋 하나가 있고 슈퍼관리자가 템플릿만 수정하면, 템플릿은 새 값이고 나머지는 그대로다"

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]:
        return Editing(query_template=RETUNED)

    @override
    def then(self) -> Then[APresetAndACaller, PresetNodeAnswer]:
        return ThePresetNode(started=self.started, query_template=RETUNED)


@dataclass(frozen=True)
class ClearingTheDescription(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "clearing-the-description-leaves-it-empty"

    @override
    def describe(self) -> str:
        return "설명이 있는 프리셋을 슈퍼관리자가 설명을 비우도록 수정하면, 설명이 없어진다"

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]:
        return Editing(clear_description=True)

    @override
    def then(self) -> Then[APresetAndACaller, PresetNodeAnswer]:
        return ThePresetNode(started=self.started, description_cleared=True)


@dataclass(frozen=True)
class MovingToAnotherCategory(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "moving-a-preset-to-another-category-points-the-node-at-that-one"

    @override
    def describe(self) -> str:
        return "카테고리 둘 중 한쪽에 속한 프리셋을 슈퍼관리자가 다른 카테고리로 옮기면, 응답의 카테고리가 그것을 가리킨다"

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetInOneOfTwoCategories(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]:
        return Editing(move_elsewhere=True)

    @override
    def then(self) -> Then[APresetAndACaller, PresetNodeAnswer]:
        return ThePresetNode(started=self.started, moved_elsewhere=True)


@dataclass(frozen=True)
class ChangingOnlyTheFilterLabels(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "changing-only-the-filter-labels-keeps-the-group-labels"

    @override
    def describe(self) -> str:
        return (
            "필터 라벨과 그룹 라벨이 모두 있는 프리셋을 슈퍼관리자가 필터 라벨만 수정하면, "
            "필터 라벨은 새 값이고 그룹 라벨은 그대로다"
        )

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(
            role=UserRole.SUPERADMIN, filter_labels=("kernel_id",), group_labels=("agent_id",)
        )

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]:
        return Editing(filter_labels=("session_id",))

    @override
    def then(self) -> Then[APresetAndACaller, PresetNodeAnswer]:
        return ThePresetNode(started=self.started, filter_labels=("session_id",))


@dataclass(frozen=True)
class GivingNothingChangesNothing(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "an-update-giving-no-value-answers-the-node-unchanged"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 값을 하나도 지정하지 않고 수정하면, 아무것도 바뀌지 않은 노드가 반환된다"
        )

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]:
        return Editing()

    @override
    def then(self) -> Then[APresetAndACaller, PresetNodeAnswer]:
        return ThePresetNode(started=self.started)


@dataclass(frozen=True)
class AnUnrenderableTemplateIsRefused(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]
):
    @override
    def summary(self) -> str:
        return "a-template-the-renderer-refuses-cannot-replace-the-stored-one"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 렌더러가 받지 않는 템플릿으로 수정하면, 템플릿 오류로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]:
        return Editing(query_template=UNRENDERABLE)

    @override
    def then(self) -> Then[APresetAndACaller, PresetNodeAnswer]:
        return TheCallIsRefused(InvalidMetricPresetTemplate)


@dataclass(frozen=True)
class AStoredBadTemplateDoesNotBlockOtherChanges(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-stored-template-the-renderer-refuses-does-not-block-renaming"

    @override
    def describe(self) -> str:
        return (
            "렌더러가 받지 않는 템플릿을 가진 프리셋을 슈퍼관리자가 이름만 수정하면, 이름은 새 값이다. "
            "템플릿 검증은 요청이 템플릿을 지정한 때만 실행된다"
        )

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN, query_template=UNRENDERABLE)

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]:
        return Editing(named=RENAMED)

    @override
    def then(self) -> Then[APresetAndACaller, PresetNodeAnswer]:
        return ThePresetNode(started=self.started, named=RENAMED)


@dataclass(frozen=True)
class AnUnknownCategoryIsRefused(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]
):
    @override
    def summary(self) -> str:
        return "moving-a-preset-to-a-category-id-nothing-answers-to-is-refused"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 존재하지 않는 카테고리 id로 수정하면, 카테고리가 없다는 이유로 거부된다. "
            "저장소의 참조 제약이 막는 것이고 도메인 오류로 옮겨져 있지 않다"
        )

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]:
        return Editing(under_an_unknown_category=True)

    @override
    def then(self) -> Then[APresetAndACaller, PresetNodeAnswer]:
        return TheCallIsRefused(ForeignKeyViolationError)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotEdit(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-edit-a-preset"

    @override
    def describe(self) -> str:
        return (
            "같은 프리셋이 있고 아무 권한도 없는 사용자가 이름을 수정하면, 권한 부족으로 "
            "거부된다. 이 엔티티는 어느 스코프에도 속하지 않아 권한을 받을 방법이 없다"
        )

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone()

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]:
        return Editing(named=RENAMED)

    @override
    def then(self) -> Then[APresetAndACaller, PresetNodeAnswer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class EnforcementOffLetsAnyoneEdit(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer],
    Configured,
):
    started: datetime

    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-a-user-edit-a-preset"

    @override
    def describe(self) -> str:
        return (
            "권한 검사를 끄면 아무 권한도 없는 사용자도 프리셋을 수정할 수 있다. "
            "수정은 역할이 아니라 권한 그래프로 보호되기 때문이다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone()

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]:
        return Editing(named=RENAMED)

    @override
    def then(self) -> Then[APresetAndACaller, PresetNodeAnswer]:
        return ThePresetNode(started=self.started, named=RENAMED)


@dataclass(frozen=True)
class AnUnknownIdIsNotFoundForASuperadmin(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]
):
    @override
    def summary(self) -> str:
        return "editing-an-id-nothing-answers-to-is-not-found-for-a-superadmin"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 존재하지 않는 id의 이름을 수정하면, 대상을 찾을 수 없다는 이유로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]:
        return Editing(named=RENAMED, other=uuid4())

    @override
    def then(self) -> Then[APresetAndACaller, PresetNodeAnswer]:
        return TheCallIsRefused(EntityNotFoundError)


SCENARIOS: list[EditingStep] = [
    TheSuperadminRetunesTheTemplate(started=datetime.now(UTC)),
    ClearingTheDescription(started=datetime.now(UTC)),
    MovingToAnotherCategory(started=datetime.now(UTC)),
    ChangingOnlyTheFilterLabels(started=datetime.now(UTC)),
    GivingNothingChangesNothing(started=datetime.now(UTC)),
    AnUnrenderableTemplateIsRefused(),
    AStoredBadTemplateDoesNotBlockOtherChanges(started=datetime.now(UTC)),
    AnUnknownCategoryIsRefused(),
    AUserGrantedNothingMayNotEdit(),
    EnforcementOffLetsAnyoneEdit(started=datetime.now(UTC)),
    AnUnknownIdIsNotFoundForASuperadmin(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing(
    scenario: EditingStep, adapter: PrometheusQueryPresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
