"""라벨 하나를 설정 — 한 엔티티의 키 하나를 쓰거나 값만 바꾼다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.entity.types import EntityTarget
from ai.backend.common.dto.manager.v2.entity_label.request import UpsertEntityLabelInput
from ai.backend.common.dto.manager.v2.entity_label.response import (
    UpsertEntityLabelPayload,
)
from ai.backend.manager.api.adapters.entity_label.adapter import EntityLabelAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
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

type Upserted = UpsertEntityLabelPayload
type UpsertStep = Scenario[
    TestSeedingSession, LabeledDomainsAndACaller, EntityLabelAdapter, Upserted
]

AFTER = "after"
"""요청이 쓰는 값."""


@dataclass(frozen=True)
class UpsertingOneLabel(When[LabeledDomainsAndACaller, EntityLabelAdapter, Upserted]):
    """대상 도메인 하나에 키 하나를 쓴다."""

    key: str
    value: str = AFTER

    @override
    def operation(self) -> str:
        return "upsert"

    @override
    def describe(self, laid: LabeledDomainsAndACaller) -> str:
        target = laid.targets[0]
        return Says(
            f"{laid.caller.username}이 도메인 {target.name}에 라벨 {self.key}={self.value}를 붙입니다",
            english=(
                f"{laid.caller.username} puts the label {self.key}={self.value} on "
                f"domain {target.name}"
            ),
        )

    @override
    async def call(self, adapter: EntityLabelAdapter, laid: LabeledDomainsAndACaller) -> Upserted:
        target = laid.targets[0]
        with ActingAs(laid.caller):
            return await adapter.upsert(
                UpsertEntityLabelInput(
                    target=EntityTarget(entity_type=LABELED, entity_id=target.id),
                    key=self.key,
                    value=self.value,
                )
            )


@dataclass(frozen=True)
class TheLabelIsWritten(Then[LabeledDomainsAndACaller, Upserted]):
    """그 라벨이 붙은 채로 온다. 미리 붙은 키였다면 같은 라벨의 값만 바뀐다."""

    started: datetime
    key: str
    value: str = AFTER
    replaced: bool = False

    @override
    def says(self) -> str:
        if self.replaced:
            return Says(
                "이미 붙은 같은 라벨의 값만 바뀌어 옵니다",
                english="the same label comes back with only its value replaced",
            )
        return Says(
            "붙은 라벨 하나가 통째로 옵니다",
            english="the whole label that was put on the entity comes back",
        )

    @override
    def look(
        self, laid: LabeledDomainsAndACaller, answered: Answered[Upserted]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        target = laid.targets[0]
        prior = laid.labels[0] if self.replaced else None
        return LabelLook(self.started).verdicts(
            "label.", payload.label, target, self.key, self.value, prior
        )


@dataclass(frozen=True)
class UpsertingRow(
    Scenario[TestSeedingSession, LabeledDomainsAndACaller, EntityLabelAdapter, Upserted]
):
    """한 행. 상황과 쓰려는 키, 값, 미리 붙은 키를 바꾸는지의 여부만 다르다."""

    named: str
    guarantees: str
    situation: LabeledDomainsAndSomeone
    key: str
    started: datetime
    replaced: bool = False

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
    def when(self) -> When[LabeledDomainsAndACaller, EntityLabelAdapter, Upserted]:
        return UpsertingOneLabel(key=self.key)

    @override
    def then(self) -> Then[LabeledDomainsAndACaller, Upserted]:
        return TheLabelIsWritten(
            started=self.started, key=self.key, replaced=self.replaced
        )


@dataclass(frozen=True)
class AUserGrantedNothingIsRefused(
    Scenario[TestSeedingSession, LabeledDomainsAndACaller, EntityLabelAdapter, Upserted]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-cannot-put-a-label-on-the-domain"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 도메인에 라벨을 붙이면 권한 부족으로 거부됩니다",
            english=(
                "when a user with no permission puts a label on a domain, the call is rejected "
                "for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, LabeledDomainsAndACaller]:
        return LabeledDomainsAndSomeone(targets=1)

    @override
    def when(self) -> When[LabeledDomainsAndACaller, EntityLabelAdapter, Upserted]:
        return UpsertingOneLabel(key="team")

    @override
    def then(self) -> Then[LabeledDomainsAndACaller, Upserted]:
        return TheCallIsRefused(NotEnoughPermission)


STARTED = datetime.now(UTC)

SCENARIOS: list[UpsertStep] = [
    UpsertingRow(
        named="a-writer-puts-a-new-key-on-an-entity",
        guarantees=Says(
            "수정 권한을 받은 사용자가 도메인에 새 키를 붙이면 그 라벨이 통째로 옵니다",
            english=(
                "when a user granted update permission puts a new key on a domain, the whole "
                "label comes back"
            ),
        ),
        situation=LabeledDomainsAndSomeone(targets=1, writable=1),
        key="team",
        started=STARTED,
    ),
    UpsertingRow(
        named="a-writer-replaces-the-value-of-an-existing-key",
        guarantees=Says(
            "수정 권한을 받은 사용자가 이미 붙은 키를 다시 쓰면 같은 라벨의 값만 바뀌어 옵니다",
            english=(
                "when a user granted update permission writes a key that is already attached, "
                "the same label comes back with only its value replaced"
            ),
        ),
        situation=LabeledDomainsAndSomeone(targets=1, writable=1, keys=("team",)),
        key="team",
        started=STARTED,
        replaced=True,
    ),
    AUserGrantedNothingIsRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_upserting(
    scenario: UpsertStep, adapter: EntityLabelAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
