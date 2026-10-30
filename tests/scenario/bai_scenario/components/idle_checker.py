"""What an idle checker or idle checker assignment scenario table says besides the call.

A checker lives in the global catalog. An assignment is a relation between a scope and a
checker; the tables here bind one checker to several domains.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.idle_checker import IdleCheckerAssignmentID, IdleCheckerID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.query import UUIDFilter
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.idle_checker.response import (
    IdleCheckerNode,
    IdleCheckerSpecInfo,
    SessionLifetimeSpecInfo,
)
from ai.backend.common.dto.manager.v2.idle_checker.types import IdleCheckerTypeDTO
from ai.backend.common.dto.manager.v2.idle_checker_assignment.request import (
    IdleCheckerAssignmentFilter,
    SearchIdleCheckerAssignmentsInput,
)
from ai.backend.common.dto.manager.v2.idle_checker_assignment.response import (
    IdleCheckerAssignmentNode,
)
from ai.backend.common.dto.manager.v2.idle_checker_assignment.types import IdleCheckerScopeTypeDTO
from ai.backend.manager.api.adapters.idle_checker_assignment.adapter import (
    IdleCheckerAssignmentAdapter,
)
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.idle_checker.types import IdleCheckerData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Then,
    Verdict,
)
from bai_scenario.components.domain import WAS_HERE, Mentions, WrittenByThisRun
from bai_scenario.components.system import lay_a_caller, role_named
from bai_scenario.runner.acting import ActingAs
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.idle_checker.checker import AssignToDomain, TestSeedIdleChecker


@dataclass(frozen=True)
class CheckersAndACaller:
    """미리 만들어 둔 검사기 여럿과, 호출자 한 명."""

    laid: tuple[IdleCheckerData, ...]
    caller: UserData


@dataclass(frozen=True)
class SomeCheckersAndSomeone(Given[Any, CheckersAndACaller]):
    """검사기 여럿과 호출자 한 명."""

    role: UserRole = UserRole.USER
    count: int = 2

    @override
    def describe(self) -> str:
        return f"유휴 검사기 {self.count}개와, {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> CheckersAndACaller:
        checkers = [await seeding.creating(TestSeedIdleChecker()) for _ in range(self.count)]
        caller = await lay_a_caller(seeding, self.role)
        return CheckersAndACaller(
            laid=tuple(seeding.made(one) for one in checkers), caller=seeding.made(caller)
        )


@dataclass(frozen=True)
class AssignmentsAndACaller:
    """도메인 여럿에 켜 둔 검사기 하나와, 할당 id 를 찾는 슈퍼관리자, 호출자."""

    checker: IdleCheckerData
    domains: tuple[DomainData, ...]
    operator: UserData
    caller: UserData


@dataclass(frozen=True)
class OneCheckerOnSomeDomains(Given[Any, AssignmentsAndACaller]):
    """검사기 하나를 도메인 여럿에 켜 두고, 호출자 한 명을 둔다."""

    role: UserRole = UserRole.USER
    count: int = 2

    @override
    def describe(self) -> str:
        return f"도메인 {self.count}개에 켜 둔 유휴 검사기 하나와, {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> AssignmentsAndACaller:
        checker = await seeding.creating(TestSeedIdleChecker())
        domains = [
            await seeding.creating(TestSeedDomain(name_hint="scope", description=WAS_HERE))
            for _ in range(self.count)
        ]
        for domain in domains:
            await seeding.linking(AssignToDomain(), domain, checker)
        operator = await lay_a_caller(seeding, UserRole.SUPERADMIN)
        caller = (
            operator if self.role == UserRole.SUPERADMIN else await lay_a_caller(seeding, self.role)
        )
        return AssignmentsAndACaller(
            checker=seeding.made(checker),
            domains=tuple(seeding.made(one) for one in domains),
            operator=seeding.made(operator),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class AssignmentsAnswered:
    """요청에 넣은 할당 id 와, 그 요청의 답."""

    ids: tuple[IdleCheckerAssignmentID, ...]
    payload: PartialBulkPayload[IdleCheckerAssignmentNode]


async def assignment_ids(
    adapter: IdleCheckerAssignmentAdapter, laid: AssignmentsAndACaller
) -> tuple[IdleCheckerAssignmentID, ...]:
    """The ids the database gave the laid assignments, in the order of their domains."""
    with ActingAs(laid.operator):
        page = await adapter.admin_search(
            SearchIdleCheckerAssignmentsInput(
                filter=IdleCheckerAssignmentFilter(
                    idle_checker_id=UUIDFilter(equals=laid.checker.id)
                )
            )
        )
    by_scope = {node.scope_id: node.id for node in page.items}
    return tuple(by_scope[domain.id] for domain in laid.domains)


def checker_node_of(seeded: IdleCheckerData) -> IdleCheckerNode:
    """The node a write on this seeded checker has to answer, whole."""
    lifetime = seeded.spec.session_lifetime
    return IdleCheckerNode(
        id=seeded.id,
        entity_id=seeded.id,
        name=seeded.name,
        description=seeded.description,
        checker_type=IdleCheckerTypeDTO(seeded.checker_type.value),
        target_session_types=seeded.target_session_types,
        initial_grace_period_seconds=seeded.initial_grace_period_seconds,
        spec=IdleCheckerSpecInfo(
            type=IdleCheckerTypeDTO(seeded.spec.type.value),
            session_lifetime=(
                SessionLifetimeSpecInfo(max_lifetime_seconds=lifetime.max_lifetime_seconds)
                if lifetime is not None
                else None
            ),
        ),
        created_at=seeded.created_at,
        updated_at=seeded.updated_at,
    )


@dataclass(frozen=True)
class EveryCheckerIsPurged(Then[CheckersAndACaller, PartialBulkPayload[IdleCheckerNode]]):
    """심은 검사기가 모두 지운 모습으로 처리된 목록에 온다. `missing`은 실패 목록에 온다."""

    missing: UUID

    @override
    def says(self) -> str:
        return "심은 검사기가 모두 지운 모습으로 오고, 없는 id 는 대상 없음 이유로 실패 목록에 온다"

    @override
    def look(
        self,
        laid: CheckersAndACaller,
        answered: Answered[PartialBulkPayload[IdleCheckerNode]],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Same("successes count", len(payload.successes), len(laid.laid)),
            Same("failed count", len(payload.failed), 1),
        ]
        for i, (node, checker) in enumerate(zip(payload.successes, laid.laid, strict=False)):
            verdicts.append(
                Held[IdleCheckerNode](
                    f"successes[{i}]",
                    node,
                    SameAs(checker_node_of(checker), f"{i + 1}번째로 심은 검사기 전체"),
                )
            )
        for failure in payload.failed:
            verdicts += [
                Held[UUID]("failed[0].id", failure.id, SameAs(self.missing, "요청에 넣은 없는 id")),
                Held("failed[0].message", failure.message, Mentions("not found")),
            ]
        return verdicts


@dataclass(frozen=True)
class NoCheckerIsPurged(Then[CheckersAndACaller, PartialBulkPayload[IdleCheckerNode]]):
    """지운 검사기 없이, 대상이 모두 같은 이유로 실패 목록에 온다."""

    reason: str

    @override
    def says(self) -> str:
        return "지운 검사기 없이 대상이 모두 실패 목록에 온다"

    @override
    def look(
        self,
        laid: CheckersAndACaller,
        answered: Answered[PartialBulkPayload[IdleCheckerNode]],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Same("successes", payload.successes, []),
            Same("failed count", len(payload.failed), len(laid.laid)),
        ]
        for i, (failure, checker) in enumerate(zip(payload.failed, laid.laid, strict=False)):
            verdicts += [
                Held[UUID](
                    f"failed[{i}].id", failure.id, SameAs(checker.id, f"{i + 1}번째로 심은 검사기")
                ),
                Held(f"failed[{i}].message", failure.message, Mentions(self.reason)),
            ]
        return verdicts


@dataclass(frozen=True)
class EveryAssignmentComesBack(Then[AssignmentsAndACaller, AssignmentsAnswered]):
    """요청한 할당이 모두 처리된 목록에 온다. `missing`이 있으면 그 id 만 실패 목록에 온다."""

    started: datetime
    enabled: bool
    missing: UUID | None = None

    @override
    def says(self) -> str:
        state = "켜진" if self.enabled else "꺼진"
        if self.missing is None:
            return f"요청한 할당이 모두 {state} 상태로 오고, 실패한 것은 없다"
        return (
            f"요청한 할당이 모두 {state} 상태로 오고, 없는 id 는 대상 없음 이유로 실패 목록에 온다"
        )

    @override
    def look(
        self, laid: AssignmentsAndACaller, answered: Answered[AssignmentsAnswered]
    ) -> list[Verdict]:
        answer = answered.response
        if answer is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        payload = answer.payload
        written = WrittenByThisRun(self.started)
        verdicts: list[Verdict] = [
            Same("successes count", len(payload.successes), len(laid.domains))
        ]
        for i, (node, domain) in enumerate(zip(payload.successes, laid.domains, strict=False)):
            verdicts += [
                Held[UUID](
                    f"successes[{i}].id",
                    node.id,
                    SameAs(answer.ids[i], f"요청에 넣은 {i + 1}번째 id"),
                ),
                Same(f"successes[{i}].scope_type", node.scope_type, IdleCheckerScopeTypeDTO.DOMAIN),
                Held[UUID](
                    f"successes[{i}].scope_id",
                    node.scope_id,
                    SameAs(domain.id, f"{i + 1}번째로 심은 도메인"),
                ),
                Held[IdleCheckerID](
                    f"successes[{i}].idle_checker_id",
                    node.idle_checker_id,
                    SameAs(laid.checker.id, "심은 검사기"),
                ),
                Same(f"successes[{i}].enabled", node.enabled, self.enabled),
                Held(f"successes[{i}].created_at", node.created_at, written),
                Held(f"successes[{i}].updated_at", node.updated_at, written),
            ]
        if self.missing is None:
            return [*verdicts, Same("failed", payload.failed, [])]
        verdicts.append(Same("failed count", len(payload.failed), 1))
        for failure in payload.failed:
            verdicts += [
                Held[UUID]("failed[0].id", failure.id, SameAs(self.missing, "요청에 넣은 없는 id")),
                Held(
                    "failed[0].message",
                    failure.message,
                    Mentions("No such idle checker assignment"),
                ),
            ]
        return verdicts


@dataclass(frozen=True)
class NoAssignmentIsProcessed(Then[AssignmentsAndACaller, AssignmentsAnswered]):
    """처리된 할당 없이, 요청한 할당이 모두 같은 이유로 실패 목록에 온다."""

    reason: str

    @override
    def says(self) -> str:
        return "처리된 할당 없이 요청한 할당이 모두 실패 목록에 온다"

    @override
    def look(
        self, laid: AssignmentsAndACaller, answered: Answered[AssignmentsAnswered]
    ) -> list[Verdict]:
        answer = answered.response
        if answer is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        payload = answer.payload
        verdicts: list[Verdict] = [
            Same("successes", payload.successes, []),
            Same("failed count", len(payload.failed), len(answer.ids)),
        ]
        for i, failure in enumerate(payload.failed):
            verdicts += [
                Held[UUID](
                    f"failed[{i}].id",
                    failure.id,
                    SameAs(answer.ids[i], f"요청에 넣은 {i + 1}번째 id"),
                ),
                Held(f"failed[{i}].message", failure.message, Mentions(self.reason)),
            ]
        return verdicts
