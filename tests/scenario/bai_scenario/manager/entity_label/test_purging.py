"""라벨 하나를 영구 삭제 — 라벨 id 로 부르고, 붙어 있던 엔티티가 답한다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.entity.entity_label import EntityLabelID
from ai.backend.common.dto.manager.v2.entity_label.response import PurgeEntityLabelPayload
from ai.backend.manager.api.adapters.entity_label.adapter import EntityLabelAdapter
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    SameAs,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.entity_label import (
    LabeledDomainsAndACaller,
    LabeledDomainsAndSomeone,
    LabelLook,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Purged = PurgeEntityLabelPayload
type PurgeStep = Scenario[
    TestSeedingSession, LabeledDomainsAndACaller, EntityLabelAdapter, Purged
]

MISSING = UUID(int=9)
"""어떤 라벨도 갖지 않은 id."""


@dataclass(frozen=True)
class PurgingOneLabel(When[LabeledDomainsAndACaller, EntityLabelAdapter, Purged]):
    """미리 붙인 라벨의 id 하나로 영구 삭제한다. ``missing``이면 없는 id 를 준다."""

    missing: bool = False

    @override
    def operation(self) -> str:
        return "purge"

    @override
    def describe(self, laid: LabeledDomainsAndACaller) -> str:
        if self.missing:
            return Says(
                f"{laid.caller.username}이 없는 라벨 id 하나를 영구 삭제합니다",
                english=f"{laid.caller.username} purges one unknown label id",
            )
        return Says(
            f"{laid.caller.username}이 붙은 키 {laid.labels[0].key}의 라벨을 영구 삭제합니다",
            english=(
                f"{laid.caller.username} purges the label under key {laid.labels[0].key}"
            ),
        )

    @override
    async def call(self, adapter: EntityLabelAdapter, laid: LabeledDomainsAndACaller) -> Purged:
        label_id = EntityLabelID(MISSING if self.missing else laid.labels[0].id)
        with ActingAs(laid.caller):
            return await adapter.purge(label_id)


@dataclass(frozen=True)
class TheLabelIsTakenOff(Then[LabeledDomainsAndACaller, Purged]):
    """떼어 낸 라벨이 통째로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "영구 삭제된 라벨이 통째로 옵니다",
            english="the label that was purged comes back whole",
        )

    @override
    def look(self, laid: LabeledDomainsAndACaller, answered: Answered[Purged]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        label = laid.labels[0]
        verdicts: list[Verdict] = LabelLook(self.started).verdicts(
            "label.", payload.label, laid.targets[0], label.key, label.value, label
        )
        verdicts.append(
            Held[UUID](
                "field_id",
                payload.field_id,
                SameAs(
                    label.id,
                    Says(
                        "미리 붙인 라벨의 id",
                        english="the id of the label attached in advance",
                    ),
                ),
            )
        )
        return verdicts


@dataclass(frozen=True)
class PurgingRow(
    Scenario[TestSeedingSession, LabeledDomainsAndACaller, EntityLabelAdapter, Purged]
):
    """한 행. 상황과, 있는 라벨을 떼는지 없는 id 를 주는지만 다르다."""

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
    def when(self) -> When[LabeledDomainsAndACaller, EntityLabelAdapter, Purged]:
        return PurgingOneLabel(missing=self.missing)

    @override
    def then(self) -> Then[LabeledDomainsAndACaller, Purged]:
        return TheLabelIsTakenOff(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingIsRefused(
    Scenario[TestSeedingSession, LabeledDomainsAndACaller, EntityLabelAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-cannot-purge-the-label"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 라벨을 영구 삭제하면 요청이 거부됩니다",
            english="when a user with no permission purges a label, the request is rejected",
        )

    @override
    def given(self) -> Given[TestSeedingSession, LabeledDomainsAndACaller]:
        return LabeledDomainsAndSomeone(targets=1, keys=("team",))

    @override
    def when(self) -> When[LabeledDomainsAndACaller, EntityLabelAdapter, Purged]:
        return PurgingOneLabel()

    @override
    def then(self) -> Then[LabeledDomainsAndACaller, Purged]:
        return TheCallIsRefused(GenericBadRequest)


@dataclass(frozen=True)
class AnUnknownIdIsRefused(
    Scenario[TestSeedingSession, LabeledDomainsAndACaller, EntityLabelAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "an-unknown-label-id-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "수정 권한을 받은 사용자가 없는 라벨 id 를 영구 삭제하면 요청이 거부됩니다",
            english=(
                "when a user granted update permission purges an unknown label id, the request "
                "is rejected"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, LabeledDomainsAndACaller]:
        return LabeledDomainsAndSomeone(targets=1, writable=1)

    @override
    def when(self) -> When[LabeledDomainsAndACaller, EntityLabelAdapter, Purged]:
        return PurgingOneLabel(missing=True)

    @override
    def then(self) -> Then[LabeledDomainsAndACaller, Purged]:
        return TheCallIsRefused(GenericBadRequest)


STARTED = datetime.now(UTC)

SCENARIOS: list[PurgeStep] = [
    PurgingRow(
        named="a-writer-purges-one-label",
        guarantees=Says(
            "수정 권한을 받은 사용자가 라벨 하나를 영구 삭제하면 그 라벨이 통째로 옵니다",
            english=(
                "when a user granted update permission purges one label, the whole label "
                "comes back"
            ),
        ),
        situation=LabeledDomainsAndSomeone(targets=1, writable=1, keys=("team",)),
        started=STARTED,
    ),
    AUserGrantedNothingIsRefused(),
    AnUnknownIdIsRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_purging(
    scenario: PurgeStep, adapter: EntityLabelAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
