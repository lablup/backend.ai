"""도메인 여럿 수정하기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.domain.request import (
    PartialBulkUpdateDomainItemInput,
    PartialBulkUpdateDomainsInput,
    UpdateDomainInput,
)
from ai.backend.common.dto.manager.v2.domain.response import DomainNode
from ai.backend.common.exception import UnreachableError
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
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import TheCallIsRefused
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

EDITED = Says("한 번에 수정한 설명", english="a description edited at once")

type Edited = PartialBulkPayload[DomainNode]
type DomainStep = Scenario[TestSeedingSession, ManyDomainsAndACaller, DomainAdapter, Edited]


@dataclass(frozen=True)
class EditingEveryTarget(When[ManyDomainsAndACaller, DomainAdapter, Edited]):
    """대상 도메인들의 설명을 한 번에 고친다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_update"

    @override
    def describe(self, laid: ManyDomainsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 도메인 {len(laid.elsewhere())}개의 설명을 한 번에 수정합니다",
            english=(
                f"{laid.caller.username} edits the description of "
                f"{len(laid.elsewhere())} domains at once"
            ),
        )

    @override
    async def call(self, adapter: DomainAdapter, laid: ManyDomainsAndACaller) -> Edited:
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_update(
                PartialBulkUpdateDomainsInput(
                    items=[
                        PartialBulkUpdateDomainItemInput(
                            id=domain.id, input=UpdateDomainInput(description=EDITED)
                        )
                        for domain in laid.elsewhere()
                    ]
                )
            )


@dataclass(frozen=True)
class EditingEveryTargetWithoutLogin(When[ManyDomainsAndACaller, DomainAdapter, Edited]):
    """로그인 문맥 없이 대상 도메인들의 설명을 한 번에 고친다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_update"

    @override
    def describe(self, laid: ManyDomainsAndACaller) -> str:
        return Says(
            f"로그인 문맥 없이 도메인 {len(laid.elsewhere())}개의 설명을 한 번에 수정합니다",
            english=(
                f"without a login context, edits the description of "
                f"{len(laid.elsewhere())} domains at once"
            ),
        )

    @override
    async def call(self, adapter: DomainAdapter, laid: ManyDomainsAndACaller) -> Edited:
        return await adapter.partial_bulk_update(
            PartialBulkUpdateDomainsInput(
                items=[
                    PartialBulkUpdateDomainItemInput(
                        id=domain.id, input=UpdateDomainInput(description=EDITED)
                    )
                    for domain in laid.elsewhere()
                ]
            )
        )


@dataclass(frozen=True)
class EveryTargetIsEdited(Then[ManyDomainsAndACaller, Edited]):
    """대상이 모두 새 설명을 싣고 처리된 목록에 오고, 실패 목록은 비어 있다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "대상 도메인이 모두 새 설명으로 오고, 실패한 것은 없습니다",
            english="every target domain comes back with the new description and none failed",
        )

    @override
    def look(self, laid: ManyDomainsAndACaller, answered: Answered[Edited]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        targets = laid.elsewhere()
        look = DomainLook(self.started, described=EDITED)
        verdicts: list[Verdict] = [
            Same("successes count", len(payload.successes), len(targets)),
            Same("failed", payload.failed, []),
        ]
        for i, (node, domain) in enumerate(zip(payload.successes, targets, strict=False)):
            verdicts += look.verdicts(f"successes[{i}].", node, domain)
        return verdicts


@dataclass(frozen=True)
class FlippingTheActiveFlagOfEach(When[ManyDomainsAndACaller, DomainAdapter, Edited]):
    """둘째 대상을 soft delete 한 뒤, 활성 플래그와 설명을 섞어 한 번에 고친다.

    첫째는 플래그를 내리고, 둘째는 올리고, `missing`은 플래그를 내린다.
    """

    missing: UUID

    @override
    def operation(self) -> str:
        return "partial_bulk_update"

    @override
    def describe(self, laid: ManyDomainsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 둘째 도메인을 soft delete 한 뒤, 첫째는 활성 플래그를 "
            "비활성화하고 둘째는 활성화하며 둘의 설명을 변경하고, 없는 id 하나의 활성 플래그를 "
            "비활성화합니다",
            english=(
                f"{laid.caller.username} soft deletes the second domain, then deactivates "
                "the active flag of the first, activates the second, changes the "
                "description of both, and deactivates the active flag of one missing id"
            ),
        )

    @override
    async def call(self, adapter: DomainAdapter, laid: ManyDomainsAndACaller) -> Edited:
        first, second = laid.elsewhere()
        with ActingAs(laid.caller):
            await adapter.delete(second.id)
            return await adapter.partial_bulk_update(
                PartialBulkUpdateDomainsInput(
                    items=[
                        PartialBulkUpdateDomainItemInput(
                            id=first.id,
                            input=UpdateDomainInput(is_active=False, description=EDITED),
                        ),
                        PartialBulkUpdateDomainItemInput(
                            id=second.id,
                            input=UpdateDomainInput(is_active=True, description=EDITED),
                        ),
                        PartialBulkUpdateDomainItemInput(
                            id=self.missing, input=UpdateDomainInput(is_active=False)
                        ),
                    ]
                )
            )


@dataclass(frozen=True)
class EachFlagIsFlipped(Then[ManyDomainsAndACaller, Edited]):
    """둘 다 새 설명으로 오고 첫째는 비활성, 둘째는 활성이다. `missing`만 실패 목록에 온다."""

    started: datetime
    missing: UUID

    @override
    def says(self) -> str:
        return Says(
            "둘 다 새 설명으로 오고 첫째는 비활성, 둘째는 활성이며, "
            "없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "both come back with the new description, the first is inactive and "
                "the second is active, and the missing id comes back in the failed list "
                "because there is no such target"
            ),
        )

    @override
    def look(self, laid: ManyDomainsAndACaller, answered: Answered[Edited]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        first, second = laid.elsewhere()
        verdicts: list[Verdict] = [Same("successes count", len(payload.successes), 2)]
        looks = [
            (DomainLook(self.started, described=EDITED, active=False), first),
            (DomainLook(self.started, described=EDITED, active=True), second),
        ]
        for i, (node, (look, domain)) in enumerate(zip(payload.successes, looks, strict=False)):
            verdicts += look.verdicts(f"successes[{i}].", node, domain)
        verdicts.append(Same("failed count", len(payload.failed), 1))
        for failure in payload.failed:
            verdicts += [
                Held[UUID](
                    "failed[0].id",
                    failure.id,
                    SameAs(
                        self.missing,
                        Says("요청에 넣은 없는 id", english="the missing id in the request"),
                    ),
                ),
                Held("failed[0].message", failure.message, Mentions("not found")),
            ]
        return verdicts


@dataclass(frozen=True)
class TheActiveFlagSoftDeletesOrRestoresEach(
    Scenario[TestSeedingSession, ManyDomainsAndACaller, DomainAdapter, Edited]
):
    started: datetime
    missing: UUID = UUID(int=1)

    @override
    def summary(self) -> str:
        return "the-active-flag-soft-deletes-or-restores-each-of-several-domains"

    @override
    def describe(self) -> str:
        return Says(
            "활성 플래그와 설명을 섞어 도메인 여럿을 한 번에 수정하면, 플래그를 비활성화한 것은 "
            "soft delete 되고 활성화한 것은 restore 되며 둘 다 새 설명으로 오고, 없는 id 는 "
            "대상이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when several domains are edited at once with a mix of active flags and "
                "descriptions, the one deactivated is soft-deleted and the one activated "
                "is restored, both come back with the new description, and the missing id "
                "comes back in the failed list because there is no such target"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyDomainsAndACaller]:
        return ManyDomainsAndSomeone(role=UserRole.SUPERADMIN, besides=1)

    @override
    def when(self) -> When[ManyDomainsAndACaller, DomainAdapter, Edited]:
        return FlippingTheActiveFlagOfEach(missing=self.missing)

    @override
    def then(self) -> Then[ManyDomainsAndACaller, Edited]:
        return EachFlagIsFlipped(started=self.started, missing=self.missing)


@dataclass(frozen=True)
class TheSuperadminEditsSeveralDomains(
    Scenario[TestSeedingSession, ManyDomainsAndACaller, DomainAdapter, Edited]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-edits-several-domains-at-once"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 도메인 여럿의 설명을 한 번에 변경하면, "
            "모두 새 설명으로 오고 실패한 것은 없습니다",
            english=(
                "when the superadmin changes the description of several domains at once, "
                "all of them come back with the new description and none failed"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyDomainsAndACaller]:
        return ManyDomainsAndSomeone(role=UserRole.SUPERADMIN, besides=1)

    @override
    def when(self) -> When[ManyDomainsAndACaller, DomainAdapter, Edited]:
        return EditingEveryTarget()

    @override
    def then(self) -> Then[ManyDomainsAndACaller, Edited]:
        return EveryTargetIsEdited(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingEditsNone(
    Scenario[TestSeedingSession, ManyDomainsAndACaller, DomainAdapter, Edited]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-edits-none-of-several-domains"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 도메인 여럿을 한 번에 수정하려 하면, "
            "수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when a user granted nothing edits several domains at once, "
                "none is edited and every one comes back in the failed list for lack "
                "of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyDomainsAndACaller]:
        return ManyDomainsAndSomeone(besides=1)

    @override
    def when(self) -> When[ManyDomainsAndACaller, DomainAdapter, Edited]:
        return EditingEveryTarget()

    @override
    def then(self) -> Then[ManyDomainsAndACaller, Edited]:
        return NothingIsProcessed(reason="Insufficient permission")


@dataclass(frozen=True)
class EditingWithoutLoginIsRefused(
    Scenario[TestSeedingSession, ManyDomainsAndACaller, DomainAdapter, Edited]
):
    @override
    def summary(self) -> str:
        return "editing-domains-without-login-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "로그인 문맥 없이 도메인 여럿을 한 번에 수정하면, 문맥에 사용자가 없다는 오류로 "
            "거부됩니다",
            english=(
                "editing several domains at once without a login context is rejected with "
                "the error saying no user is in the context"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyDomainsAndACaller]:
        return ManyDomainsAndSomeone(besides=1)

    @override
    def when(self) -> When[ManyDomainsAndACaller, DomainAdapter, Edited]:
        return EditingEveryTargetWithoutLogin()

    @override
    def then(self) -> Then[ManyDomainsAndACaller, Edited]:
        return TheCallIsRefused(UnreachableError)


SCENARIOS: list[DomainStep] = [
    TheSuperadminEditsSeveralDomains(started=datetime.now(UTC)),
    AUserGrantedNothingEditsNone(),
    TheActiveFlagSoftDeletesOrRestoresEach(started=datetime.now(UTC)),
    EditingWithoutLoginIsRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_editing(
    scenario: DomainStep, adapter: DomainAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
