"""도메인 여럿 soft delete, restore."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.domain.request import (
    PartialBulkDeleteDomainsInput,
    PartialBulkRestoreDomainsInput,
)
from ai.backend.common.dto.manager.v2.domain.response import DomainNode
from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.domain import (
    DomainLook,
    ManyDomainsAndACaller,
    ManyDomainsAndSomeone,
    Mentions,
    NothingIsProcessed,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Deleted = PartialBulkPayload[DomainNode]
type DomainStep = Scenario[TestSeedingSession, ManyDomainsAndACaller, DomainAdapter, Deleted]


@dataclass(frozen=True)
class SoftDeletingEveryTarget(When[ManyDomainsAndACaller, DomainAdapter, Deleted]):
    """대상 도메인들을 한 번에 soft delete 한다. `missing`이 있으면 그 id 도 함께 넣는다."""

    missing: UUID | None = None

    @override
    def operation(self) -> str:
        return "partial_bulk_delete"

    @override
    def describe(self, laid: ManyDomainsAndACaller) -> str:
        besides = " 와 없는 id 하나" if self.missing is not None else ""
        return f"{laid.caller.username}이 도메인 {len(laid.elsewhere())}개{besides}를 한 번에 soft delete 함"

    @override
    async def call(self, adapter: DomainAdapter, laid: ManyDomainsAndACaller) -> Deleted:
        ids: list[UUID] = [domain.id for domain in laid.elsewhere()]
        if self.missing is not None:
            ids.append(self.missing)
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_delete(PartialBulkDeleteDomainsInput(ids=ids))


@dataclass(frozen=True)
class SoftDeletingThenRestoringEveryTarget(When[ManyDomainsAndACaller, DomainAdapter, Deleted]):
    """대상 도메인들을 한 번에 soft delete 했다가 한 번에 restore 한다. restore 의 답을 준다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_restore"

    @override
    def describe(self, laid: ManyDomainsAndACaller) -> str:
        return (
            f"{laid.caller.username}이 도메인 {len(laid.elsewhere())}개를 한 번에 soft delete "
            "했다가 한 번에 restore 함"
        )

    @override
    async def call(self, adapter: DomainAdapter, laid: ManyDomainsAndACaller) -> Deleted:
        ids: list[UUID] = [domain.id for domain in laid.elsewhere()]
        with ActingAs(laid.caller):
            await adapter.partial_bulk_delete(PartialBulkDeleteDomainsInput(ids=ids))
            return await adapter.partial_bulk_restore(PartialBulkRestoreDomainsInput(ids=ids))


@dataclass(frozen=True)
class EveryTargetComesBack(Then[ManyDomainsAndACaller, Deleted]):
    """대상이 모두 처리된 목록에 온다. `missing`이 있으면 그 id 만 실패 목록에 온다."""

    started: datetime
    active: bool
    missing: UUID | None = None

    @override
    def says(self) -> str:
        state = "활성" if self.active else "비활성"
        if self.missing is None:
            return f"대상 도메인이 모두 {state}으로 오고, 실패한 것은 없다"
        return (
            f"대상 도메인이 모두 {state}으로 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def look(self, laid: ManyDomainsAndACaller, answered: Answered[Deleted]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        targets = laid.elsewhere()
        look = DomainLook(self.started, active=self.active)
        verdicts: list[Verdict] = [Same("successes count", len(payload.successes), len(targets))]
        for i, (node, domain) in enumerate(zip(payload.successes, targets, strict=False)):
            verdicts += look.verdicts(f"successes[{i}].", node, domain)
        if self.missing is None:
            return [*verdicts, Same("failed", payload.failed, [])]
        verdicts.append(Same("failed count", len(payload.failed), 1))
        for failure in payload.failed:
            verdicts += [
                Held[UUID]("failed[0].id", failure.id, SameAs(self.missing, "요청에 넣은 없는 id")),
                Held("failed[0].message", failure.message, Mentions("not found")),
            ]
        return verdicts


@dataclass(frozen=True)
class SoftDeletingAnswersForTheMissingOne(
    Scenario[TestSeedingSession, ManyDomainsAndACaller, DomainAdapter, Deleted]
):
    started: datetime
    missing: UUID = UUID(int=1)

    @override
    def summary(self) -> str:
        return "soft-deleting-several-answers-for-the-missing-one"

    @override
    def describe(self) -> str:
        return (
            "활성 도메인 둘과 없는 id 하나를 한 번에 soft delete 하면, 둘은 비활성으로 오고 "
            "없는 id 는 대상이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyDomainsAndACaller]:
        return ManyDomainsAndSomeone(role=UserRole.SUPERADMIN, besides=1)

    @override
    def when(self) -> When[ManyDomainsAndACaller, DomainAdapter, Deleted]:
        return SoftDeletingEveryTarget(missing=self.missing)

    @override
    def then(self) -> Then[ManyDomainsAndACaller, Deleted]:
        return EveryTargetComesBack(started=self.started, active=False, missing=self.missing)


@dataclass(frozen=True)
class AUserGrantedNothingSoftDeletesNone(
    Scenario[TestSeedingSession, ManyDomainsAndACaller, DomainAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-soft-deletes-none-of-several-domains"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 도메인 여럿을 한 번에 soft delete 하려 하면, "
            "soft delete 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyDomainsAndACaller]:
        return ManyDomainsAndSomeone(besides=1)

    @override
    def when(self) -> When[ManyDomainsAndACaller, DomainAdapter, Deleted]:
        return SoftDeletingEveryTarget()

    @override
    def then(self) -> Then[ManyDomainsAndACaller, Deleted]:
        return NothingIsProcessed(reason="Insufficient permission")


@dataclass(frozen=True)
class RestoringBringsSeveralBack(
    Scenario[TestSeedingSession, ManyDomainsAndACaller, DomainAdapter, Deleted]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "restoring-several-brings-them-back"

    @override
    def describe(self) -> str:
        return "soft delete 된 도메인 여럿을 한 번에 restore 하면, 모두 활성으로 온다"

    @override
    def given(self) -> Given[TestSeedingSession, ManyDomainsAndACaller]:
        return ManyDomainsAndSomeone(role=UserRole.SUPERADMIN, besides=1)

    @override
    def when(self) -> When[ManyDomainsAndACaller, DomainAdapter, Deleted]:
        return SoftDeletingThenRestoringEveryTarget()

    @override
    def then(self) -> Then[ManyDomainsAndACaller, Deleted]:
        return EveryTargetComesBack(started=self.started, active=True)


SCENARIOS: list[DomainStep] = [
    SoftDeletingAnswersForTheMissingOne(started=datetime.now(UTC)),
    AUserGrantedNothingSoftDeletesNone(),
    RestoringBringsSeveralBack(started=datetime.now(UTC)),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_deleting(
    scenario: DomainStep, adapter: DomainAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
