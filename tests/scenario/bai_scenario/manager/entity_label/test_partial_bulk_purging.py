"""라벨 여럿을 삭제."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import pytest

from ai.backend.common.dto.manager.v2.entity_label.request import (
    PartialBulkPurgeEntityLabelInput,
)
from ai.backend.common.dto.manager.v2.entity_label.response import (
    PartialBulkPurgeEntityLabelPayload,
)
from ai.backend.manager.api.adapters.entity_label.adapter import EntityLabelAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Configured,
    Given,
    Held,
    Same,
    SameAs,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse
from bai_scenario.components.app_config import ENFORCEMENT
from bai_scenario.components.domain import Mentions
from bai_scenario.components.entity_label import (
    LabeledDomainsAndACaller,
    LabeledDomainsAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Purged = PartialBulkPurgeEntityLabelPayload
type LabelStep = Scenario[TestSeedingSession, LabeledDomainsAndACaller, EntityLabelAdapter, Purged]

MISSING = (UUID(int=1), UUID(int=2))
"""어떤 라벨도 갖지 않은 id."""


@dataclass(frozen=True)
class PurgingTheLaidLabels(When[LabeledDomainsAndACaller, EntityLabelAdapter, Purged]):
    """미리 붙인 라벨을 한 번에 뗀다. ``missing``개의 없는 id 를 뒤에 붙인다."""

    missing: int = 0

    @override
    def operation(self) -> str:
        return "partial_bulk_purge"

    @override
    def describe(self, laid: LabeledDomainsAndACaller) -> str:
        if self.missing:
            return Says(
                f"{laid.caller.username}이 라벨 {len(laid.labels)}개와 없는 id "
                f"{self.missing}개를 한 번에 영구 삭제합니다",
                english=(
                    f"{laid.caller.username} purges {len(laid.labels)} labels "
                    f"and {self.missing} unknown ids at once"
                ),
            )
        return Says(
            f"{laid.caller.username}이 라벨 {len(laid.labels)}개를 한 번에 영구 삭제합니다",
            english=f"{laid.caller.username} purges {len(laid.labels)} labels at once",
        )

    @override
    async def call(self, adapter: EntityLabelAdapter, laid: LabeledDomainsAndACaller) -> Purged:
        ids = [label.id for label in laid.labels] + list(MISSING[: self.missing])
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_purge(PartialBulkPurgeEntityLabelInput(ids=ids))


@dataclass(frozen=True)
class PurgedAndRefused(Then[LabeledDomainsAndACaller, Purged]):
    """앞에서부터 ``purged``개 라벨이 떼어지고, 나머지 라벨과 없는 id 는 실패 목록에 온다."""

    purged: int
    reason: str
    missing: int = 0

    @override
    def says(self) -> str:
        if self.missing:
            unknown = "the unknown id" if self.missing == 1 else "the unknown ids"
            return Says(
                f"라벨 {self.purged}개가 영구 삭제된 채 오고, 없는 id 는 대상이 없다는 이유로 "
                "실패 목록에 옵니다",
                english=(
                    f"{self.purged} labels come back purged, and {unknown} come back "
                    "in the failed list as not found"
                ),
            )
        return Says(
            f"라벨 {self.purged}개가 영구 삭제된 채 오고, 나머지는 실패 목록에 옵니다",
            english=(
                f"{self.purged} labels come back purged and the rest come back in the failed list"
            ),
        )

    @override
    def look(self, laid: LabeledDomainsAndACaller, answered: Answered[Purged]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        purged = laid.labels[: self.purged]
        refused = [label.id for label in laid.labels[self.purged :]]
        verdicts: list[Verdict] = [Same("successes count", len(payload.successes), len(purged))]
        for i, (got, label) in enumerate(zip(payload.successes, purged, strict=False)):
            verdicts.append(
                Held[UUID](
                    f"successes[{i}]",
                    got,
                    SameAs(
                        label.id,
                        Says(
                            "미리 붙인 라벨의 id",
                            english="the id of the label attached in advance",
                        ),
                    ),
                )
            )
        failed = [*refused, *MISSING[: self.missing]]
        verdicts.append(Same("failed count", len(payload.failed), len(failed)))
        for i, (failure, label_id) in enumerate(zip(payload.failed, failed, strict=False)):
            reason = self.reason if label_id in refused else "not found"
            verdicts += [
                Held[UUID](
                    f"failed[{i}].id",
                    failure.id,
                    SameAs(
                        label_id,
                        Says("요청에 넣은 id", english="the id put in the request"),
                    ),
                ),
                Held(f"failed[{i}].message", failure.message, Mentions(reason)),
            ]
        return verdicts


@dataclass(frozen=True)
class PurgingRow(
    Scenario[TestSeedingSession, LabeledDomainsAndACaller, EntityLabelAdapter, Purged]
):
    """한 행. 상황, 없는 id 의 개수, 몇 개의 라벨이 떼어져야 하는지만 다르다."""

    named: str
    guarantees: str
    situation: LabeledDomainsAndSomeone
    purged: int
    reason: str = "Insufficient permission"
    missing: int = 0

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
        return PurgingTheLaidLabels(missing=self.missing)

    @override
    def then(self) -> Then[LabeledDomainsAndACaller, Purged]:
        return PurgedAndRefused(purged=self.purged, reason=self.reason, missing=self.missing)


@dataclass(frozen=True)
class EnforcementOffRow(PurgingRow, Configured):
    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}


SCENARIOS: list[LabelStep] = [
    PurgingRow(
        named="a-writer-purges-two-labels-of-one-entity",
        guarantees=Says(
            "수정 권한을 받은 사용자가 한 엔티티의 라벨 둘을 영구 삭제하면 둘 다 영구 "
            "삭제되고 실패한 것은 없습니다",
            english=(
                "when a user granted update permission purges two labels of one entity, "
                "both are purged and nothing failed"
            ),
        ),
        situation=LabeledDomainsAndSomeone(targets=1, writable=1, keys=("team", "tier")),
        purged=2,
    ),
    PurgingRow(
        named="a-writer-purges-labels-of-two-entities",
        guarantees=Says(
            "엔티티 둘에 붙은 라벨을 하나씩 영구 삭제하면 둘 다 영구 삭제됩니다",
            english="purging one label on each of two entities purges both",
        ),
        situation=LabeledDomainsAndSomeone(writable=2, keys=("team",)),
        purged=2,
    ),
    PurgingRow(
        named="only-the-label-of-the-writable-entity-is-purged",
        guarantees=Says(
            "한 엔티티에만 수정 권한이 있으면 그 엔티티의 라벨만 영구 삭제되고 다른 쪽은 "
            "실패 목록에 옵니다",
            english=(
                "with update permission on one entity only, only that entity's label is "
                "purged and the other comes back in the failed list"
            ),
        ),
        situation=LabeledDomainsAndSomeone(writable=1, keys=("team",)),
        purged=1,
    ),
    PurgingRow(
        named="a-missing-id-beside-a-label-is-one-failed-item",
        guarantees=Says(
            "있는 id 뒤에 없는 id 를 붙여 영구 삭제하면 있는 것은 영구 삭제되고 없는 id 는 "
            "실패 목록에 옵니다",
            english=(
                "purging an existing id followed by an unknown id purges the one that exists "
                "and puts the unknown id in the failed list"
            ),
        ),
        situation=LabeledDomainsAndSomeone(targets=1, writable=1, keys=("team",)),
        purged=1,
        missing=1,
    ),
    PurgingRow(
        named="every-id-missing-is-answered-per-id",
        guarantees=Says(
            "없는 id 만 둘 영구 삭제하면 영구 삭제된 것 없이 둘 다 실패 목록에 옵니다",
            english="purging only two unknown ids purges nothing and puts both in the failed list",
        ),
        situation=LabeledDomainsAndSomeone(targets=1, writable=1),
        purged=0,
        missing=2,
    ),
    PurgingRow(
        named="a-user-granted-nothing-purges-nothing",
        guarantees=Says(
            "아무 권한도 없는 사용자가 라벨 둘을 영구 삭제하면 영구 삭제된 것 없이 둘 다 "
            "실패 목록에 옵니다",
            english=(
                "when a user with no permission purges two labels, nothing is purged and "
                "both come back in the failed list"
            ),
        ),
        situation=LabeledDomainsAndSomeone(targets=1, keys=("team", "tier")),
        purged=0,
    ),
    EnforcementOffRow(
        named="turning-enforcement-off-lets-anyone-purge",
        guarantees=Says(
            "RBAC 강제를 끄면 아무 권한도 없는 사용자도 라벨 둘을 영구 삭제합니다",
            english=(
                "turning RBAC enforcement off lets a user with no permission purge two labels"
            ),
        ),
        situation=LabeledDomainsAndSomeone(targets=1, keys=("team", "tier")),
        purged=2,
    ),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_purging(
    scenario: LabelStep, adapter: EntityLabelAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
