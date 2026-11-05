"""로그인 클라이언트 종류 조회 — id로 조회한다. 인증만 확인한다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import uuid4

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.login_client_type.response import LoginClientTypeNode
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.api.adapters.login_client_type.adapter import LoginClientTypeAdapter
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
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.domain import WrittenByThisRun
from bai_scenario.components.login_client_type import (
    ATypeAndACaller,
    ATypeAndSomeone,
    ManyTypesAndACaller,
    ManyTypesAndSomeone,
    TheTypeNode,
    type_verdicts,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type ReadingStep = Scenario[
    TestSeedingSession, ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode
]
type Loaded = list[LoginClientTypeNode | Exception | None]
type LoadingStep = Scenario[TestSeedingSession, ManyTypesAndACaller, LoginClientTypeAdapter, Loaded]


@dataclass(frozen=True)
class ReadingById(When[ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]):
    """id로 조회한다. ``unknown``이면 어느 행에도 없는 id를 쓴다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: ATypeAndACaller) -> str:
        if self.unknown:
            target_ko = "존재하지 않는 id"
            target_en = "an id nothing answers to"
        else:
            target_ko = laid.client_type.name
            target_en = laid.client_type.name
        return Says(
            f"{laid.caller.username} 이 {target_ko} (으)로 조회합니다",
            english=f"{laid.caller.username} reads a login client type by {target_en}",
        )

    @override
    async def call(
        self, adapter: LoginClientTypeAdapter, laid: ATypeAndACaller
    ) -> LoginClientTypeNode:
        with ActingAs(laid.caller):
            return await adapter.get(uuid4() if self.unknown else laid.client_type.id)


@dataclass(frozen=True)
class AUserGrantedNothingReadsById(
    Scenario[TestSeedingSession, ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-reads-a-login-client-type-by-id"

    @override
    def describe(self) -> str:
        return Says(
            (
                "아무 권한도 없는 사용자가 id 로 조회하면 그 로그인 클라이언트 유형 전체가 "
                "반환됩니다. 이 조회는 인증만 확인합니다"
            ),
            english=(
                "when a user granted nothing reads a login client type by id, the whole login "
                "client type comes back. This read checks authentication alone"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ATypeAndACaller]:
        return ATypeAndSomeone()

    @override
    def when(self) -> When[ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]:
        return ReadingById()

    @override
    def then(self) -> Then[ATypeAndACaller, LoginClientTypeNode]:
        return TheTypeNode(started=self.started)


@dataclass(frozen=True)
class AnIdNothingAnswersToIsRefused(
    Scenario[TestSeedingSession, ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]
):
    @override
    def summary(self) -> str:
        return "reading-a-login-client-type-id-nothing-answers-to-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "존재하지 않는 id 로 조회하면 대상을 찾을 수 없다는 이유로 거부됩니다",
            english=(
                "when it is read by an id nothing answers to, it is rejected because the target "
                "cannot be found"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ATypeAndACaller]:
        return ATypeAndSomeone()

    @override
    def when(self) -> When[ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]:
        return ReadingById(unknown=True)

    @override
    def then(self) -> Then[ATypeAndACaller, LoginClientTypeNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class LoadingTheLaidAndAMissingOne(When[ManyTypesAndACaller, LoginClientTypeAdapter, Loaded]):
    """미리 저장한 종류들의 id 뒤에 없는 id 하나를 붙여 한 번에 조회한다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: ManyTypesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 미리 저장한 종류 {len(laid.laid)}개와 없는 id 하나를 "
            "한 번에 조회합니다",
            english=(
                f"{laid.caller.username} batch-loads the {len(laid.laid)} login client types "
                "created in advance and one unknown id"
            ),
        )

    @override
    async def call(self, adapter: LoginClientTypeAdapter, laid: ManyTypesAndACaller) -> Loaded:
        ids: list = [*(one.id for one in laid.laid), uuid4()]
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids(ids)


@dataclass(frozen=True)
class LoadingAsNobody(When[ManyTypesAndACaller, LoginClientTypeAdapter, Loaded]):
    """사용자 컨텍스트 없이 한 번에 조회한다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: ManyTypesAndACaller) -> str:
        return Says(
            f"사용자 컨텍스트 없이 종류 {len(laid.laid)}개를 한 번에 조회합니다",
            english=f"batch-loads {len(laid.laid)} login client types without a user context",
        )

    @override
    async def call(self, adapter: LoginClientTypeAdapter, laid: ManyTypesAndACaller) -> Loaded:
        return await adapter.batch_load_by_ids([one.id for one in laid.laid])


@dataclass(frozen=True)
class TheyComeBackInTheOrderAsked(Then[ManyTypesAndACaller, Loaded]):
    """요청한 순서대로 한 항목씩 반환되고, 없는 id 에 해당하는 항목은 비어 있습니다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "요청한 순서대로 반환되고, 없는 id 에 해당하는 항목은 비어 있습니다",
            english="they come back in the order asked and the item for an unknown id is empty",
        )

    @override
    def look(self, laid: ManyTypesAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [Refused(UnreachableError, answered.raised)]
        asked = len(laid.laid) + 1
        seen: list[Verdict] = [Same("len(items)", len(items), asked)]
        for i, client_type in enumerate(laid.laid):
            got = items[i] if i < len(items) else None
            if not isinstance(got, LoginClientTypeNode):
                seen.append(Same(f"items[{i}]", got, Says("노드", english="a node")))
                continue
            seen.extend(
                type_verdicts(
                    got,
                    named=client_type.name,
                    described=client_type.description,
                    written=WrittenByThisRun(self.started),
                )
            )
        last = items[asked - 1] if len(items) >= asked else "none"
        seen.append(Same(f"items[{asked - 1}]", last, None))
        return seen


@dataclass(frozen=True)
class TheSuperadminLoadsLaidAndMissing(
    Scenario[TestSeedingSession, ManyTypesAndACaller, LoginClientTypeAdapter, Loaded]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-batch-load-leaves-a-missing-id-empty"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 미리 저장한 종류 둘과 없는 id 하나를 한 번에 조회하면, "
            "요청한 순서대로 반환되고 없는 id 에 해당하는 항목은 비어 있습니다",
            english=(
                "when the superadmin batch-loads two login client types created in advance and "
                "one unknown id, they come back in the order asked and the item for the "
                "unknown id is empty"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyTypesAndACaller]:
        return ManyTypesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyTypesAndACaller, LoginClientTypeAdapter, Loaded]:
        return LoadingTheLaidAndAMissingOne()

    @override
    def then(self) -> Then[ManyTypesAndACaller, Loaded]:
        return TheyComeBackInTheOrderAsked(started=self.started)


@dataclass(frozen=True)
class ABatchLoadCarryingNoUserIsRefused(
    Scenario[TestSeedingSession, ManyTypesAndACaller, LoginClientTypeAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-batch-load-carrying-no-user-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "종류 둘이 있고 사용자 컨텍스트 없이 한 번에 조회하면, 호출자를 알 수 없어 거부됩니다",
            english=(
                "when two login client types exist and they are batch-loaded without a user "
                "context, it is rejected because the caller cannot be known"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyTypesAndACaller]:
        return ManyTypesAndSomeone()

    @override
    def when(self) -> When[ManyTypesAndACaller, LoginClientTypeAdapter, Loaded]:
        return LoadingAsNobody()

    @override
    def then(self) -> Then[ManyTypesAndACaller, Loaded]:
        return TheCallIsRefused(UnreachableError)


SCENARIOS: list[ReadingStep | LoadingStep] = [
    AUserGrantedNothingReadsById(started=datetime.now(UTC)),
    AnIdNothingAnswersToIsRefused(),
    TheSuperadminLoadsLaidAndMissing(started=datetime.now(UTC)),
    ABatchLoadCarryingNoUserIsRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadingStep, adapter: LoginClientTypeAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
