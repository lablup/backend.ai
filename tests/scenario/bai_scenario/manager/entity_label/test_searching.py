"""붙은 라벨을 훑기 — 엔티티 여럿을 범위로 주거나, 이미 쥔 엔티티 하나로 부른다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.types import RuntimeEntityID
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.entity.types import EntityTarget
from ai.backend.common.dto.manager.v2.entity_label.request import (
    EntityLabelFilter,
    EntityLabelPageInput,
    SearchEntityLabelsInput,
)
from ai.backend.common.dto.manager.v2.entity_label.response import (
    SearchEntityLabelsPayload,
)
from ai.backend.manager.api.adapters.entity_label.adapter import EntityLabelAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Same,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.entity_label import (
    LABELED,
    LabeledDomainsAndACaller,
    LabeledDomainsAndSomeone,
    LabelLook,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Found = SearchEntityLabelsPayload
type SearchStep = Scenario[TestSeedingSession, LabeledDomainsAndACaller, EntityLabelAdapter, Found]


@dataclass(frozen=True)
class SearchingTheNamedScopes(When[LabeledDomainsAndACaller, EntityLabelAdapter, Found]):
    """대상 도메인들을 범위로 주고 훑는다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: LabeledDomainsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 도메인 {len(laid.targets)}개의 라벨을 한 번에 훑습니다",
            english=(
                f"{laid.caller.username} pages through the labels of "
                f"{len(laid.targets)} domains at once"
            ),
        )

    @override
    async def call(self, adapter: EntityLabelAdapter, laid: LabeledDomainsAndACaller) -> Found:
        with ActingAs(laid.caller):
            return await adapter.search(
                SearchEntityLabelsInput(
                    scope=[
                        EntityTarget(entity_type=LABELED, entity_id=target.id)
                        for target in laid.targets
                    ]
                )
            )


@dataclass(frozen=True)
class SearchingOneHeldScope(When[LabeledDomainsAndACaller, EntityLabelAdapter, Found]):
    """이미 쥔 도메인 하나의 라벨을 훑는다. 키 하나로 좁힌다."""

    key: str

    @override
    def operation(self) -> str:
        return "search_on"

    @override
    def describe(self, laid: LabeledDomainsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 도메인 {laid.targets[0].name}의 라벨 중 "
            f"{self.key} 키만 훑습니다",
            english=(
                f"{laid.caller.username} pages through the labels under key {self.key} "
                f"on domain {laid.targets[0].name}"
            ),
        )

    @override
    async def call(self, adapter: EntityLabelAdapter, laid: LabeledDomainsAndACaller) -> Found:
        target = laid.targets[0]
        with ActingAs(laid.caller):
            return await adapter.search_on(
                RuntimeEntityID(DomainEntityType(), target.id),
                EntityLabelPageInput(filter=EntityLabelFilter(key=StringFilter(equals=self.key))),
            )


@dataclass(frozen=True)
class ThePickedLabels(Then[LabeledDomainsAndACaller, Found]):
    """상황이 붙인 라벨 중 고른 것들이 빠짐없이, 각자 통째로 온다."""

    started: datetime
    picked: tuple[int, ...]

    @override
    def says(self) -> str:
        return Says(
            f"미리 붙인 라벨 {len(self.picked)}개가 빠짐없이 통째로 옵니다",
            english=(
                f"every one of the {len(self.picked)} labels attached in advance comes back whole"
            ),
        )

    @override
    def look(self, laid: LabeledDomainsAndACaller, answered: Answered[Found]) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [MissingResponse(answered.raised)]
        verdicts: list[Verdict] = [
            Same("items count", len(page.items), len(self.picked)),
            Same("total_count", page.total_count, len(self.picked)),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]
        by_label = {(node.entity_id, node.key): node for node in page.items}
        for i, at in enumerate(self.picked):
            label = laid.labels[at]
            node = by_label.get((label.entity, label.key))
            verdicts.append(Same(f"items[{i}].present", node is not None, True))
            if node is None:
                continue
            domain = next(one for one in laid.targets if one.id == label.entity)
            verdicts += LabelLook(self.started).verdicts(
                f"items[{i}].", node, domain, label.key, label.value, label
            )
        return verdicts


@dataclass(frozen=True)
class SearchRow(Scenario[TestSeedingSession, LabeledDomainsAndACaller, EntityLabelAdapter, Found]):
    """한 행. 어떤 상황에서 어느 범위를 훑는지만 다르다."""

    named: str
    guarantees: str
    situation: LabeledDomainsAndSomeone
    started: datetime
    picked: tuple[int, ...]
    held_key: str | None = None
    """값이 있으면 ``search_on`` 으로 그 키만 훑는다."""

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
    def when(self) -> When[LabeledDomainsAndACaller, EntityLabelAdapter, Found]:
        if self.held_key is not None:
            return SearchingOneHeldScope(key=self.held_key)
        return SearchingTheNamedScopes()

    @override
    def then(self) -> Then[LabeledDomainsAndACaller, Found]:
        return ThePickedLabels(started=self.started, picked=self.picked)


@dataclass(frozen=True)
class NoPermissionRow(
    Scenario[TestSeedingSession, LabeledDomainsAndACaller, EntityLabelAdapter, Found]
):
    """라벨을 읽을 권한이 없어 훑기가 거부되는 행."""

    named: str
    guarantees: str
    held: bool

    @override
    def summary(self) -> str:
        return self.named

    @override
    def describe(self) -> str:
        return self.guarantees

    @override
    def given(self) -> Given[TestSeedingSession, LabeledDomainsAndACaller]:
        return LabeledDomainsAndSomeone(targets=1, keys=("team",))

    @override
    def when(self) -> When[LabeledDomainsAndACaller, EntityLabelAdapter, Found]:
        if self.held:
            return SearchingOneHeldScope(key="team")
        return SearchingTheNamedScopes()

    @override
    def then(self) -> Then[LabeledDomainsAndACaller, Found]:
        return TheCallIsRefused(NotEnoughPermission)


STARTED = datetime.now(UTC)

SCENARIOS: list[SearchStep] = [
    SearchRow(
        named="a-reader-pages-through-the-labels-of-two-entities",
        guarantees=Says(
            "도메인 둘을 읽을 수 있는 사용자가 두 도메인의 라벨을 한 번에 훑으면, 붙인 라벨 "
            "둘이 모두 통째로 옵니다",
            english=(
                "when a user who can read two domains pages through both at once, both labels "
                "come back whole"
            ),
        ),
        situation=LabeledDomainsAndSomeone(targets=2, readable=2, keys=("team",)),
        started=STARTED,
        picked=(0, 1),
    ),
    SearchRow(
        named="a-reader-pages-through-one-entities-labels-under-a-key",
        guarantees=Says(
            "도메인 하나를 읽을 수 있는 사용자가 이미 쥔 그 도메인의 라벨을 키 하나로 좁혀 "
            "훑으면, 그 키의 라벨만 옵니다",
            english=(
                "when a user who can read one domain pages through it narrowed to one key, "
                "only that key's label comes back"
            ),
        ),
        situation=LabeledDomainsAndSomeone(targets=1, readable=1, keys=("tier", "team")),
        started=STARTED,
        picked=(1,),
        held_key="team",
    ),
    NoPermissionRow(
        named="a-user-granted-nothing-cannot-page-through-the-named-scopes",
        guarantees=Says(
            "아무 권한도 없는 사용자가 도메인의 라벨을 훑으면 권한 부족으로 거부됩니다",
            english=(
                "when a user with no permission pages through a domain's labels, the call is "
                "rejected for lack of permission"
            ),
        ),
        held=False,
    ),
    NoPermissionRow(
        named="a-user-granted-nothing-cannot-page-through-a-held-scope",
        guarantees=Says(
            "아무 권한도 없는 사용자가 이미 쥔 도메인의 라벨을 훑어도 권한 부족으로 거부됩니다",
            english=(
                "when a user with no permission pages through a held domain's labels, the call "
                "is rejected for lack of permission"
            ),
        ),
        held=True,
    ),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchStep, adapter: EntityLabelAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
