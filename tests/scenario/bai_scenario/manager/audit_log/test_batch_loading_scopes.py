"""여러 id로 범위 조회 — 기록이 남긴 범위를 id마다 항목으로 응답한다.

없는 id는 빈 항목이다. 기록의 범위를 먼저 검색해 id를 읽는다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.audit_log import AuditLogID, AuditLogScopeID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.audit_log.request import SearchAuditLogScopesInput
from ai.backend.common.dto.manager.v2.audit_log.response import AuditLogScopeEntryNode
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.api.adapters.audit_log.adapter import AuditLogAdapter
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
from bai_scenario.components.audit_log import AScopedRecord, ScopesToSearch
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type ScopeLoaded = list[AuditLogScopeEntryNode | Exception | None]


@dataclass(frozen=True)
class ScopeSlotsAnswered:
    """요청에 넣은 범위 id 순서와, 그 요청의 답."""

    entries: tuple[AuditLogScopeEntryNode, ...]
    loaded: ScopeLoaded


@dataclass(frozen=True)
class LoadingTheScopesAndAMissingOne(When[ScopesToSearch, AuditLogAdapter, ScopeSlotsAnswered]):
    """기록이 남긴 범위 id 뒤에 없는 id 하나를 붙여 한 번에 조회한다."""

    @override
    def operation(self) -> str:
        return "batch_load_scopes_by_ids"

    @override
    def describe(self, laid: ScopesToSearch) -> str:
        return Says(
            f"{laid.caller.username}이 기록 하나의 범위와 없는 id 하나를 한 번에 조회합니다",
            english=(
                f"{laid.caller.username} reads the scopes of one record and one unknown id "
                "at once"
            ),
        )

    @override
    async def call(self, adapter: AuditLogAdapter, laid: ScopesToSearch) -> ScopeSlotsAnswered:
        with ActingAs(laid.caller):
            scopes = await adapter.search_scopes(
                AuditLogID(laid.record), SearchAuditLogScopesInput()
            )
            loaded = await adapter.batch_load_scopes_by_ids([
                *(AuditLogScopeID(one.id) for one in scopes.items),
                AuditLogScopeID(uuid4()),
            ])
        return ScopeSlotsAnswered(entries=tuple(scopes.items), loaded=loaded)


@dataclass(frozen=True)
class LoadingScopesAsNobody(When[ScopesToSearch, AuditLogAdapter, ScopeSlotsAnswered]):
    """사용자 컨텍스트 없이 한 번에 조회한다."""

    @override
    def operation(self) -> str:
        return "batch_load_scopes_by_ids"

    @override
    def describe(self, laid: ScopesToSearch) -> str:
        return Says(
            "사용자 컨텍스트 없이 기록 하나의 범위를 한 번에 조회합니다",
            english="reads the scopes of one record at once without a user context",
        )

    @override
    async def call(self, adapter: AuditLogAdapter, laid: ScopesToSearch) -> ScopeSlotsAnswered:
        with ActingAs(laid.caller):
            scopes = await adapter.search_scopes(
                AuditLogID(laid.record), SearchAuditLogScopesInput()
            )
        loaded = await adapter.batch_load_scopes_by_ids([
            AuditLogScopeID(one.id) for one in scopes.items
        ])
        return ScopeSlotsAnswered(entries=tuple(scopes.items), loaded=loaded)


@dataclass(frozen=True)
class TheScopesComeBackInTheOrderAsked(Then[ScopesToSearch, ScopeSlotsAnswered]):
    """요청한 순서대로 한 항목씩 반환되고, 없는 id 에 해당하는 항목은 비어 있습니다."""

    @override
    def says(self) -> str:
        return Says(
            "요청한 순서대로 반환되고, 없는 id 에 해당하는 항목은 비어 있습니다",
            english="they come back in the order asked and the item for an unknown id is empty",
        )

    @override
    def look(
        self, laid: ScopesToSearch, answered: Answered[ScopeSlotsAnswered]
    ) -> list[Verdict]:
        answer = answered.response
        if answer is None:
            return [Refused(UnreachableError, answered.raised)]
        loaded = answer.loaded
        seen: list[Verdict] = [Same("len(items)", len(loaded), len(answer.entries) + 1)]
        for i, entry in enumerate(answer.entries):
            got = loaded[i] if i < len(loaded) else None
            if not isinstance(got, AuditLogScopeEntryNode):
                seen.append(Same(f"items[{i}]", got, Says("노드", english="a node")))
                continue
            seen += [
                Same(f"items[{i}].id", got.id, entry.id),
                Same(f"items[{i}].field_id", got.field_id, entry.field_id),
                Same(f"items[{i}].audit_log_id", got.audit_log_id, entry.audit_log_id),
                Same(f"items[{i}].scope_type", got.scope_type, entry.scope_type),
                Same(f"items[{i}].scope_id", got.scope_id, entry.scope_id),
            ]
        last = loaded[len(answer.entries)] if len(loaded) > len(answer.entries) else "none"
        seen.append(Same(f"items[{len(answer.entries)}]", last, None))
        return seen


@dataclass(frozen=True)
class TheSuperadminLoadsTheScopesAndMissing(
    Scenario[TestSeedingSession, ScopesToSearch, AuditLogAdapter, ScopeSlotsAnswered]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-batch-load-leaves-a-missing-scope-id-empty"

    @override
    def describe(self) -> str:
        return Says(
            "범위 둘을 남긴 기록을 superadmin 이 그 범위들과 없는 id 하나를 한 번에 조회하면, "
            "요청한 순서대로 반환되고 없는 id 에 해당하는 항목은 비어 있습니다",
            english=(
                "when the superadmin batch-loads the two scopes a record left and one unknown "
                "id, they come back in the order asked and the item for the unknown id is empty"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ScopesToSearch]:
        return AScopedRecord(reader="superadmin")

    @override
    def when(self) -> When[ScopesToSearch, AuditLogAdapter, ScopeSlotsAnswered]:
        return LoadingTheScopesAndAMissingOne()

    @override
    def then(self) -> Then[ScopesToSearch, ScopeSlotsAnswered]:
        return TheScopesComeBackInTheOrderAsked()


@dataclass(frozen=True)
class AScopeLoadCarryingNoUserIsRefused(
    Scenario[TestSeedingSession, ScopesToSearch, AuditLogAdapter, ScopeSlotsAnswered]
):
    @override
    def summary(self) -> str:
        return "a-scope-load-carrying-no-user-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "범위가 있고 사용자 컨텍스트 없이 한 번에 조회하면, 호출자를 알 수 없어 거부됩니다",
            english=(
                "when scopes exist and they are batch-loaded without a user context, "
                "it is rejected because the caller cannot be known"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ScopesToSearch]:
        return AScopedRecord()

    @override
    def when(self) -> When[ScopesToSearch, AuditLogAdapter, ScopeSlotsAnswered]:
        return LoadingScopesAsNobody()

    @override
    def then(self) -> Then[ScopesToSearch, ScopeSlotsAnswered]:
        return TheCallIsRefused(UnreachableError)


SCENARIOS: list[Scenario[TestSeedingSession, ScopesToSearch, AuditLogAdapter, ScopeSlotsAnswered]] = [
    TheSuperadminLoadsTheScopesAndMissing(),
    AScopeLoadCarryingNoUserIsRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_batch_loading_scopes(
    scenario: Scenario[TestSeedingSession, ScopesToSearch, AuditLogAdapter, ScopeSlotsAnswered],
    adapter: AuditLogAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
