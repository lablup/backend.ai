"""라벨 여럿을 설정."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.entity.types import EntityTarget
from ai.backend.common.dto.manager.v2.entity_label.request import (
    PartialBulkUpsertEntityLabelInput,
    UpsertEntityLabelInput,
)
from ai.backend.common.dto.manager.v2.entity_label.response import (
    PartialBulkUpsertEntityLabelPayload,
)
from ai.backend.manager.api.adapters.entity_label.adapter import EntityLabelAdapter
from ai.backend.manager.data.entity_label.types import EntityLabelData
from ai.backend.manager.errors.api import InvalidAPIParameters
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
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.app_config import ENFORCEMENT
from bai_scenario.components.domain import Mentions
from bai_scenario.components.entity_label import (
    LABELED,
    UNWIRED,
    LabeledDomainsAndACaller,
    LabeledDomainsAndSomeone,
    LabelLook,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Upserted = PartialBulkUpsertEntityLabelPayload
type LabelStep = Scenario[
    TestSeedingSession, LabeledDomainsAndACaller, EntityLabelAdapter, Upserted
]

AFTER = "after"
"""요청이 붙이는 값."""


@dataclass(frozen=True)
class UpsertingOnEveryTarget(When[LabeledDomainsAndACaller, EntityLabelAdapter, Upserted]):
    """대상 도메인마다 키들을 한 번에 붙인다. ``unwired``이면 배선되지 않은 타입 하나를 섞는다."""

    keys: Sequence[str]
    unwired: bool = False

    @override
    def operation(self) -> str:
        return "partial_bulk_upsert"

    @override
    def describe(self, laid: LabeledDomainsAndACaller) -> str:
        if self.unwired:
            return Says(
                f"{laid.caller.username}이 도메인 {len(laid.targets)}개와 없는 타입 하나에 키 "
                f"{len(self.keys)}개씩을 한 번에 추가합니다",
                english=(
                    f"{laid.caller.username} adds {len(self.keys)} keys each to "
                    f"{len(laid.targets)} domains and one unknown type at once"
                ),
            )
        return Says(
            f"{laid.caller.username}이 도메인 {len(laid.targets)}개에 키 "
            f"{len(self.keys)}개씩을 한 번에 추가합니다",
            english=(
                f"{laid.caller.username} adds {len(self.keys)} keys each to "
                f"{len(laid.targets)} domains at once"
            ),
        )

    @override
    async def call(self, adapter: EntityLabelAdapter, laid: LabeledDomainsAndACaller) -> Upserted:
        items = [
            UpsertEntityLabelInput(
                target=EntityTarget(entity_type=LABELED, entity_id=target.id), key=key, value=AFTER
            )
            for target in laid.targets
            for key in self.keys
        ]
        if self.unwired:
            items.append(
                UpsertEntityLabelInput(
                    target=EntityTarget(entity_type=UNWIRED, entity_id=laid.targets[0].id),
                    key=self.keys[0],
                    value=AFTER,
                )
            )
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_upsert(PartialBulkUpsertEntityLabelInput(items=items))


@dataclass(frozen=True)
class WrittenAndRefused(Then[LabeledDomainsAndACaller, Upserted]):
    """앞에서부터 ``written``개 대상의 키가 모두 붙고, 나머지 대상은 키마다 실패 항목으로 온다."""

    started: datetime
    keys: Sequence[str]
    written: int

    @override
    def says(self) -> str:
        return Says(
            f"도메인 {self.written}개에 키 {len(self.keys)}개씩 추가된 라벨이 오고, "
            "나머지 도메인은 키마다 권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                f"labels with {len(self.keys)} keys each come back for {self.written} domains, "
                "and the rest come back in the failed list per key for lack of permission"
            ),
        )

    @override
    def look(self, laid: LabeledDomainsAndACaller, answered: Answered[Upserted]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        written = laid.targets[: self.written]
        refused = laid.targets[self.written :]
        prior: dict[tuple[UUID, str], EntityLabelData] = {
            (label.entity, label.key): label for label in laid.labels
        }
        look = LabelLook(self.started)
        verdicts: list[Verdict] = [
            Same("items count", len(payload.items), len(written) * len(self.keys))
        ]
        expected = [(target, key) for target in written for key in self.keys]
        for i, (node, (target, key)) in enumerate(zip(payload.items, expected, strict=False)):
            verdicts += look.verdicts(
                f"items[{i}].", node, target, key, AFTER, prior.get((target.id, key))
            )
        failed = [(target, key) for target in refused for key in self.keys]
        verdicts.append(Same("failed count", len(payload.failed), len(failed)))
        for i, (failure, (target, key)) in enumerate(zip(payload.failed, failed, strict=False)):
            verdicts += [
                Same(f"failed[{i}].entity_type", failure.entity_type, LABELED),
                Held[UUID](
                    f"failed[{i}].entity_id",
                    failure.entity_id,
                    SameAs(
                        target.id,
                        Says("대상 도메인의 id", english="the id of the target domain"),
                    ),
                ),
                Same(f"failed[{i}].key", failure.key, key),
                Held(f"failed[{i}].message", failure.message, Mentions("Insufficient permission")),
            ]
        return verdicts


@dataclass(frozen=True)
class UpsertingRow(
    Scenario[TestSeedingSession, LabeledDomainsAndACaller, EntityLabelAdapter, Upserted]
):
    """한 행. 상황, 붙일 키, 몇 개의 대상이 쓰여야 하는지만 다르다."""

    named: str
    guarantees: str
    situation: LabeledDomainsAndSomeone
    keys: Sequence[str]
    written: int
    started: datetime

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
        return UpsertingOnEveryTarget(keys=self.keys)

    @override
    def then(self) -> Then[LabeledDomainsAndACaller, Upserted]:
        return WrittenAndRefused(started=self.started, keys=self.keys, written=self.written)


@dataclass(frozen=True)
class EnforcementOffRow(UpsertingRow, Configured):
    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}


@dataclass(frozen=True)
class AnUnwiredTypeRefusesTheWholeCall(
    Scenario[TestSeedingSession, LabeledDomainsAndACaller, EntityLabelAdapter, Upserted]
):
    @override
    def summary(self) -> str:
        return "an-unwired-type-refuses-the-whole-call"

    @override
    def describe(self) -> str:
        return Says(
            "연결 및 호출 경로로 처리되지 않는 타입이 하나라도 섞여 있으면 잘못된 요청으로 "
            "전체가 거부되고 아무것도 기록되지 않습니다",
            english=(
                "when even one type that has no connection and call path is mixed in, "
                "the whole request is rejected as invalid and nothing is written"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, LabeledDomainsAndACaller]:
        return LabeledDomainsAndSomeone(targets=1, writable=1)

    @override
    def when(self) -> When[LabeledDomainsAndACaller, EntityLabelAdapter, Upserted]:
        return UpsertingOnEveryTarget(keys=("team",), unwired=True)

    @override
    def then(self) -> Then[LabeledDomainsAndACaller, Upserted]:
        return TheCallIsRefused(InvalidAPIParameters)


def _scenarios() -> list[LabelStep]:
    started = datetime.now(UTC)
    two_keys = ("team", "tier")
    return [
        UpsertingRow(
            named="a-writer-labels-two-entities-with-two-keys",
            guarantees=Says(
                "수정 권한을 받은 사용자가 엔티티 둘에 키 둘을 추가하면 라벨 넷이 오고 "
                "실패한 것은 없습니다",
                english=(
                    "when a user granted update permission adds two keys to two entities, "
                    "four labels come back and nothing failed"
                ),
            ),
            situation=LabeledDomainsAndSomeone(writable=2),
            keys=two_keys,
            written=2,
            started=started,
        ),
        UpsertingRow(
            named="only-the-writable-entity-is-labeled",
            guarantees=Says(
                "한 엔티티에만 수정 권한이 있으면 그 엔티티의 라벨 둘이 오고, 다른 엔티티는 "
                "키마다 하나씩 실패 목록에 옵니다",
                english=(
                    "with update permission on one entity only, its two labels come back and "
                    "the other entity comes back in the failed list once per key"
                ),
            ),
            situation=LabeledDomainsAndSomeone(writable=1),
            keys=two_keys,
            written=1,
            started=started,
        ),
        UpsertingRow(
            named="a-user-granted-nothing-labels-nothing",
            guarantees=Says(
                "아무 권한도 없는 사용자가 추가하면 라벨이 추가되지 않고 엔티티 둘 다 실패 "
                "목록에 옵니다",
                english=(
                    "when a user with no permission adds labels, none is added and both "
                    "entities come back in the failed list"
                ),
            ),
            situation=LabeledDomainsAndSomeone(),
            keys=("team",),
            written=0,
            started=started,
        ),
        UpsertingRow(
            named="one-entity-in-several-items-gets-every-key",
            guarantees=Says(
                "같은 엔티티가 여러 항목에 나오면 그 엔티티의 라벨이 키마다 오고 실패한 것은 "
                "없습니다",
                english=(
                    "when the same entity appears in several items, its label comes back for "
                    "each key and nothing failed"
                ),
            ),
            situation=LabeledDomainsAndSomeone(targets=1, writable=1),
            keys=two_keys,
            written=1,
            started=started,
        ),
        UpsertingRow(
            named="a-key-already-on-the-entity-takes-the-new-value",
            guarantees=Says(
                "이미 붙은 키를 다시 추가하면 같은 라벨이 값만 바뀌어 옵니다",
                english=(
                    "adding a key that is already attached changes only the value of the same label"
                ),
            ),
            situation=LabeledDomainsAndSomeone(targets=1, writable=1, keys=("team",)),
            keys=("team",),
            written=1,
            started=started,
        ),
        AnUnwiredTypeRefusesTheWholeCall(),
        EnforcementOffRow(
            named="turning-enforcement-off-lets-anyone-label",
            guarantees=Says(
                "RBAC 강제를 끄면 아무 권한도 없는 사용자도 엔티티 둘에 라벨을 추가하고 "
                "실패한 것은 없습니다",
                english=(
                    "turning RBAC enforcement off lets a user with no permission add labels "
                    "to two entities with nothing failed"
                ),
            ),
            situation=LabeledDomainsAndSomeone(role=UserRole.USER),
            keys=("team",),
            written=2,
            started=started,
        ),
    ]


SCENARIOS: list[LabelStep] = _scenarios()


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_upserting(
    scenario: LabelStep, adapter: EntityLabelAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
