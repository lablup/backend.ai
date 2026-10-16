"""로그인 클라이언트 종류 여럿 수정하기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.login_client_type.request import (
    PartialBulkUpdateLoginClientTypeItemInput,
    PartialBulkUpdateLoginClientTypesInput,
    UpdateLoginClientTypeInput,
)
from ai.backend.common.dto.manager.v2.login_client_type.response import LoginClientTypeNode
from ai.backend.manager.api.adapters.login_client_type.adapter import LoginClientTypeAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Same,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.domain import WrittenByThisRun
from bai_scenario.components.login_client_type import (
    ManyTypesAndACaller,
    ManyTypesAndSomeone,
    NoTypeIsProcessed,
    type_verdicts,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

EDITED = "한 번에 고친 설명"

type Edited = PartialBulkPayload[LoginClientTypeNode]
type EditingStep = Scenario[TestSeedingSession, ManyTypesAndACaller, LoginClientTypeAdapter, Edited]


@dataclass(frozen=True)
class EditingEveryType(When[ManyTypesAndACaller, LoginClientTypeAdapter, Edited]):
    """미리 만들어 둔 종류들의 설명을 한 번에 고친다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_update"

    @override
    def describe(self, laid: ManyTypesAndACaller) -> str:
        return f"{laid.caller.username}이 종류 {len(laid.laid)}개의 설명을 한 번에 고침"

    @override
    async def call(self, adapter: LoginClientTypeAdapter, laid: ManyTypesAndACaller) -> Edited:
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_update(
                PartialBulkUpdateLoginClientTypesInput(
                    items=[
                        PartialBulkUpdateLoginClientTypeItemInput(
                            id=client_type.id,
                            input=UpdateLoginClientTypeInput(description=EDITED),
                        )
                        for client_type in laid.laid
                    ]
                )
            )


@dataclass(frozen=True)
class EveryTypeIsEdited(Then[ManyTypesAndACaller, Edited]):
    """종류가 모두 새 설명을 싣고 처리된 목록에 오고, 실패 목록은 비어 있다."""

    started: datetime

    @override
    def says(self) -> str:
        return "종류가 모두 새 설명으로 오고, 실패한 것은 없다"

    @override
    def look(self, laid: ManyTypesAndACaller, answered: Answered[Edited]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Same("successes count", len(payload.successes), len(laid.laid)),
            Same("failed", payload.failed, []),
        ]
        for node, client_type in zip(payload.successes, laid.laid, strict=False):
            verdicts += type_verdicts(
                node,
                named=client_type.name,
                described=EDITED,
                written=WrittenByThisRun(self.started),
            )
        return verdicts


@dataclass(frozen=True)
class TheSuperadminEditsSeveralTypes(
    Scenario[TestSeedingSession, ManyTypesAndACaller, LoginClientTypeAdapter, Edited]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-edits-several-login-client-types-at-once"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 종류 여럿의 설명을 한 번에 바꾸면, 모두 새 설명으로 오고 실패한 것은 없다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyTypesAndACaller]:
        return ManyTypesAndSomeone(role=UserRole.SUPERADMIN, besides=1)

    @override
    def when(self) -> When[ManyTypesAndACaller, LoginClientTypeAdapter, Edited]:
        return EditingEveryType()

    @override
    def then(self) -> Then[ManyTypesAndACaller, Edited]:
        return EveryTypeIsEdited(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingEditsNone(
    Scenario[TestSeedingSession, ManyTypesAndACaller, LoginClientTypeAdapter, Edited]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-edits-none-of-several-login-client-types"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 없는 사용자가 종류 여럿을 한 번에 고치려 하면, 고쳐진 것 없이 "
            "모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyTypesAndACaller]:
        return ManyTypesAndSomeone(besides=1)

    @override
    def when(self) -> When[ManyTypesAndACaller, LoginClientTypeAdapter, Edited]:
        return EditingEveryType()

    @override
    def then(self) -> Then[ManyTypesAndACaller, Edited]:
        return NoTypeIsProcessed(reason="Insufficient permission")


SCENARIOS: list[EditingStep] = [
    TheSuperadminEditsSeveralTypes(started=datetime.now(UTC)),
    AUserGrantedNothingEditsNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_editing(
    scenario: EditingStep, adapter: LoginClientTypeAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
