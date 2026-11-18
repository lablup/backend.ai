"""라벨 여럿을 id 로 한 번에 읽기 — 자리마다 노드, 거부, 빈 값이 온다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.entity.entity_label import EntityLabelID
from ai.backend.common.dto.manager.v2.entity_label.response import EntityLabelNode
from ai.backend.manager.api.adapters.entity_label.adapter import EntityLabelAdapter
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
from bai_scenario.components.answers import MissingResponse
from bai_scenario.components.entity_label import (
    LabeledDomainsAndACaller,
    LabeledDomainsAndSomeone,
    LabelLook,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Answer = list[EntityLabelNode | Exception | None]
type LoadStep = Scenario[TestSeedingSession, LabeledDomainsAndACaller, EntityLabelAdapter, Answer]

MISSING = UUID(int=9)
"""어떤 라벨도 갖지 않은 id."""


@dataclass(frozen=True)
class LoadingTheLabels(When[LabeledDomainsAndACaller, EntityLabelAdapter, Answer]):
    """미리 붙인 라벨들의 id 를 한 번에 읽는다. ``missing``이면 없는 id 를 뒤에 붙인다."""

    missing: bool = False
    empty: bool = False

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: LabeledDomainsAndACaller) -> str:
        if self.empty:
            return Says(
                f"{laid.caller.username}이 빈 id 목록으로 일괄 조회합니다",
                english=f"{laid.caller.username} loads with an empty id list",
            )
        if self.missing:
            return Says(
                f"{laid.caller.username}이 라벨 {len(laid.labels)}개와 없는 id 하나를 한 번에 "
                "조회합니다",
                english=(
                    f"{laid.caller.username} loads {len(laid.labels)} labels and one unknown id "
                    "at once"
                ),
            )
        return Says(
            f"{laid.caller.username}이 라벨 {len(laid.labels)}개를 한 번에 조회합니다",
            english=f"{laid.caller.username} loads {len(laid.labels)} labels at once",
        )

    @override
    async def call(self, adapter: EntityLabelAdapter, laid: LabeledDomainsAndACaller) -> Answer:
        if self.empty:
            return await adapter.batch_load_by_ids([])
        ids = [EntityLabelID(label.id) for label in laid.labels]
        if self.missing:
            ids.append(EntityLabelID(MISSING))
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids(ids)


@dataclass(frozen=True)
class TheNodesComeBack(Then[LabeledDomainsAndACaller, Answer]):
    """미리 붙인 라벨이 입력 순서대로 노드로 온다. 없는 id 자리는 빈 값이다."""

    started: datetime
    missing: bool = False

    @override
    def says(self) -> str:
        if self.missing:
            return Says(
                "미리 붙인 라벨은 노드로, 없는 id 자리는 빈 값으로 옵니다",
                english=(
                    "the labels attached in advance come back as nodes and the unknown id "
                    "entry as an empty value"
                ),
            )
        return Says(
            "미리 붙인 라벨이 입력 순서대로 노드로 옵니다",
            english="the labels attached in advance come back as nodes in input order",
        )

    @override
    def look(self, laid: LabeledDomainsAndACaller, answered: Answered[Answer]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        expected = len(laid.labels) + (1 if self.missing else 0)
        verdicts: list[Verdict] = [Same("length", len(loaded), expected)]
        if len(loaded) != expected:
            return verdicts
        for i, label in enumerate(laid.labels):
            node = loaded[i]
            if isinstance(node, EntityLabelNode):
                verdicts += LabelLook(self.started).verdicts(
                    f"[{i}].", node, laid.targets[0], label.key, label.value, label
                )
            else:
                verdicts.append(Same(f"[{i}]", type(node).__name__, "EntityLabelNode"))
        if self.missing:
            verdicts.append(Same(f"[{len(laid.labels)}]", loaded[-1], None))
        return verdicts


@dataclass(frozen=True)
class TheLabelIsRefused(Then[LabeledDomainsAndACaller, Answer]):
    """호출은 성공하고, 그 자리는 권한 부족으로 거부된다."""

    @override
    def says(self) -> str:
        return Says(
            "그 항목은 권한 부족으로 거부됩니다",
            english="that entry is rejected for lack of permission",
        )

    @override
    def look(self, laid: LabeledDomainsAndACaller, answered: Answered[Answer]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        first = loaded[0] if loaded else None
        return [
            Same("length", len(loaded), 1),
            Refused(NotEnoughPermission, first if isinstance(first, Exception) else None),
        ]


@dataclass(frozen=True)
class AnEmptyList(Then[LabeledDomainsAndACaller, Answer]):
    """빈 목록이 온다."""

    @override
    def says(self) -> str:
        return Says("빈 목록이 옵니다", english="an empty list comes back")

    @override
    def look(self, laid: LabeledDomainsAndACaller, answered: Answered[Answer]) -> list[Verdict]:
        if answered.response is None:
            return [MissingResponse(answered.raised)]
        return [Same("loaded", answered.response, [])]


@dataclass(frozen=True)
class LoadingRow(
    Scenario[TestSeedingSession, LabeledDomainsAndACaller, EntityLabelAdapter, Answer]
):
    named: str
    guarantees: str
    situation: LabeledDomainsAndSomeone
    started: datetime
    missing: bool = False

    @override
    def summary(self) -> str:
        return self.named

    @override
    def describe(self) -> str:
        return self.guarantees

    @override
    def given(self) -> Given[TestSeedingSession, LabeledDomainsAndACaller]:
        return self.situation

    @override
    def when(self) -> When[LabeledDomainsAndACaller, EntityLabelAdapter, Answer]:
        return LoadingTheLabels(missing=self.missing)

    @override
    def then(self) -> Then[LabeledDomainsAndACaller, Answer]:
        return TheNodesComeBack(started=self.started, missing=self.missing)


@dataclass(frozen=True)
class AUserGrantedNothingGetsARefusal(
    Scenario[TestSeedingSession, LabeledDomainsAndACaller, EntityLabelAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-gets-a-rejection-for-the-label"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 라벨을 id 로 일괄 조회하면, 호출은 성공하되 그 항목은 "
            "권한 부족으로 거부됩니다",
            english=(
                "when a user with no permission loads a label by id, the call succeeds but "
                "that entry is rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, LabeledDomainsAndACaller]:
        return LabeledDomainsAndSomeone(targets=1, keys=("team",))

    @override
    def when(self) -> When[LabeledDomainsAndACaller, EntityLabelAdapter, Answer]:
        return LoadingTheLabels()

    @override
    def then(self) -> Then[LabeledDomainsAndACaller, Answer]:
        return TheLabelIsRefused()


@dataclass(frozen=True)
class ALoadOfNothingAnswersNothing(
    Scenario[TestSeedingSession, LabeledDomainsAndACaller, EntityLabelAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-batch-load-of-no-ids-answers-an-empty-list"

    @override
    def describe(self) -> str:
        return Says(
            "빈 id 목록을 주면 권한 검사 없이 빈 목록이 옵니다",
            english="when an empty id list is given, an empty list comes back without a check",
        )

    @override
    def given(self) -> Given[TestSeedingSession, LabeledDomainsAndACaller]:
        return LabeledDomainsAndSomeone(targets=1)

    @override
    def when(self) -> When[LabeledDomainsAndACaller, EntityLabelAdapter, Answer]:
        return LoadingTheLabels(empty=True)

    @override
    def then(self) -> Then[LabeledDomainsAndACaller, Answer]:
        return AnEmptyList()


STARTED = datetime.now(UTC)

SCENARIOS: list[LoadStep] = [
    LoadingRow(
        named="a-reader-loads-two-labels-and-an-unknown-id-in-order",
        guarantees=Says(
            "도메인을 읽을 수 있는 사용자가 라벨 둘과 없는 id 하나를 한 번에 조회하면, 입력 "
            "순서대로 라벨 둘과 빈 값이 옵니다",
            english=(
                "when a user who can read the domains loads two labels and one unknown id at "
                "once, the two labels and an empty value come back in input order"
            ),
        ),
        situation=LabeledDomainsAndSomeone(targets=1, readable=1, keys=("team", "tier")),
        started=STARTED,
        missing=True,
    ),
    AUserGrantedNothingGetsARefusal(),
    ALoadOfNothingAnswersNothing(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_batch_loading(
    scenario: LoadStep, adapter: EntityLabelAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
