"""로그인 클라이언트 종류 여럿 purge."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.login_client_type.request import (
    PartialBulkPurgeLoginClientTypesInput,
)
from ai.backend.common.dto.manager.v2.login_client_type.response import LoginClientTypeNode
from ai.backend.manager.api.adapters.login_client_type.adapter import LoginClientTypeAdapter
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
from bai_scenario.components.domain import Mentions, WrittenByThisRun
from bai_scenario.components.login_client_type import (
    ManyTypesAndACaller,
    ManyTypesAndSomeone,
    NoTypeIsProcessed,
    type_verdicts,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Purged = PartialBulkPayload[LoginClientTypeNode]
type PurgingStep = Scenario[TestSeedingSession, ManyTypesAndACaller, LoginClientTypeAdapter, Purged]


@dataclass(frozen=True)
class PurgingEveryType(When[ManyTypesAndACaller, LoginClientTypeAdapter, Purged]):
    """미리 만들어 둔 종류들을 한 번에 purge 한다. `missing`이 있으면 그 id 도 함께 넣는다."""

    missing: UUID | None = None

    @override
    def operation(self) -> str:
        return "partial_bulk_purge"

    @override
    def describe(self, laid: ManyTypesAndACaller) -> str:
        besides = " 와 없는 id 하나" if self.missing is not None else ""
        return f"{laid.caller.username}이 종류 {len(laid.laid)}개{besides}를 한 번에 purge 함"

    @override
    async def call(self, adapter: LoginClientTypeAdapter, laid: ManyTypesAndACaller) -> Purged:
        ids: list[UUID] = [client_type.id for client_type in laid.laid]
        if self.missing is not None:
            ids.append(self.missing)
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_purge(PartialBulkPurgeLoginClientTypesInput(ids=ids))


@dataclass(frozen=True)
class EveryTypeIsPurged(Then[ManyTypesAndACaller, Purged]):
    """종류가 모두 지워지기 전 모습으로 처리된 목록에 오고, 없는 id 만 실패 목록에 온다."""

    started: datetime
    missing: UUID

    @override
    def says(self) -> str:
        return "종류가 모두 처리된 목록에 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 온다"

    @override
    def look(self, laid: ManyTypesAndACaller, answered: Answered[Purged]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Same("successes count", len(payload.successes), len(laid.laid)),
        ]
        for node, client_type in zip(payload.successes, laid.laid, strict=False):
            verdicts += type_verdicts(
                node,
                named=client_type.name,
                described=client_type.description,
                written=WrittenByThisRun(self.started),
            )
        verdicts.append(Same("failed count", len(payload.failed), 1))
        for failure in payload.failed:
            verdicts += [
                Held[UUID]("failed[0].id", failure.id, SameAs(self.missing, "요청에 넣은 없는 id")),
                Held("failed[0].message", failure.message, Mentions("not found")),
            ]
        return verdicts


@dataclass(frozen=True)
class PurgingAnswersForTheMissingOne(
    Scenario[TestSeedingSession, ManyTypesAndACaller, LoginClientTypeAdapter, Purged]
):
    started: datetime
    missing: UUID = UUID(int=1)

    @override
    def summary(self) -> str:
        return "purging-several-login-client-types-answers-for-the-missing-one"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 종류 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 처리된 목록에 오고 "
            "없는 id 는 대상이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyTypesAndACaller]:
        return ManyTypesAndSomeone(role=UserRole.SUPERADMIN, besides=1)

    @override
    def when(self) -> When[ManyTypesAndACaller, LoginClientTypeAdapter, Purged]:
        return PurgingEveryType(missing=self.missing)

    @override
    def then(self) -> Then[ManyTypesAndACaller, Purged]:
        return EveryTypeIsPurged(started=self.started, missing=self.missing)


@dataclass(frozen=True)
class AUserGrantedNothingPurgesNone(
    Scenario[TestSeedingSession, ManyTypesAndACaller, LoginClientTypeAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-purges-none-of-several-login-client-types"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 없는 사용자가 종류 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 "
            "모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyTypesAndACaller]:
        return ManyTypesAndSomeone(besides=1)

    @override
    def when(self) -> When[ManyTypesAndACaller, LoginClientTypeAdapter, Purged]:
        return PurgingEveryType()

    @override
    def then(self) -> Then[ManyTypesAndACaller, Purged]:
        return NoTypeIsProcessed(reason="Insufficient permission")


SCENARIOS: list[PurgingStep] = [
    PurgingAnswersForTheMissingOne(started=datetime.now(UTC)),
    AUserGrantedNothingPurgesNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_purging(
    scenario: PurgingStep, adapter: LoginClientTypeAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
