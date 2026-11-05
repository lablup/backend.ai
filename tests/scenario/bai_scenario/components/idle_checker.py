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
    SearchIdleCheckerAssignmentPayload,
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
    Language,
    Refused,
    Same,
    SameAs,
    Says,
    Then,
    Verdict,
    in_language,
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
        who = role_named(self.role)
        return Says(
            f"유휴 검사기 {self.count}개와, {who} 한 명",
            english=f"{self.count} idle checkers and one {in_language(who, Language.ENGLISH)}",
        )

    @override
    async def lay(self, seeding: Any) -> CheckersAndACaller:
        checkers = [await seeding.creating(TestSeedIdleChecker()) for _ in range(self.count)]
        caller = await lay_a_caller(seeding, self.role)
        return CheckersAndACaller(
            laid=tuple(seeding.made(one) for one in checkers), caller=seeding.made(caller)
        )


@dataclass(frozen=True)
class ACheckerAndADomainAndACaller:
    """도메인에 켜지 않은 검사기 하나와 도메인 하나, 호출자 한 명."""

    checker: IdleCheckerData
    domain: DomainData
    caller: UserData


@dataclass(frozen=True)
class ACheckerAndADomain(Given[Any, ACheckerAndADomainAndACaller]):
    """검사기 하나와 도메인 하나, 호출자 한 명을 둔다."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        who = role_named(self.role)
        return Says(
            f"유휴 검사기 하나와 도메인 하나, {who} 한 명",
            english=(f"one idle checker, one domain and one {in_language(who, Language.ENGLISH)}"),
        )

    @override
    async def lay(self, seeding: Any) -> ACheckerAndADomainAndACaller:
        checker = await seeding.creating(TestSeedIdleChecker())
        domain = await seeding.creating(TestSeedDomain(name_hint="scope", description=WAS_HERE))
        caller = await lay_a_caller(seeding, self.role)
        return ACheckerAndADomainAndACaller(
            checker=seeding.made(checker),
            domain=seeding.made(domain),
            caller=seeding.made(caller),
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
        who = role_named(self.role)
        return Says(
            f"도메인 {self.count}개에 활성화해 둔 유휴 검사기 하나와, {who} 한 명",
            english=(
                f"one idle checker enabled on {self.count} domains and one "
                f"{in_language(who, Language.ENGLISH)}"
            ),
        )

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
    payload: SearchIdleCheckerAssignmentPayload


@dataclass(frozen=True)
class PartialBulkAnswered:
    """partial bulk 호출에 넣은 할당 id 와, 그 호출의 답."""

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
        return Says(
            "미리 저장한 검사기가 모두 삭제된 모습으로 오고, 없는 id 는 대상이 없다는 이유로 "
            "실패 목록에 옵니다",
            english=(
                "every checker seeded in advance comes back deleted and an unknown id comes back "
                "in the failed list because no target answers to it"
            ),
        )

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
                    SameAs(
                        checker_node_of(checker),
                        Says(
                            f"{i + 1}번째로 미리 저장한 검사기 전체",
                            english=f"the whole checker seeded in advance number {i + 1}",
                        ),
                    ),
                )
            )
        for failure in payload.failed:
            verdicts += [
                Held[UUID](
                    "failed[0].id",
                    failure.id,
                    SameAs(
                        self.missing,
                        Says("요청에 넣은 없는 id", english="the unknown id put in the request"),
                    ),
                ),
                Held("failed[0].message", failure.message, Mentions("not found")),
            ]
        return verdicts


@dataclass(frozen=True)
class NoCheckerIsPurged(Then[CheckersAndACaller, PartialBulkPayload[IdleCheckerNode]]):
    """지운 검사기 없이, 대상이 모두 같은 이유로 실패 목록에 온다."""

    reason: str

    @override
    def says(self) -> str:
        return Says(
            "삭제한 검사기 없이 대상이 모두 실패 목록에 옵니다",
            english="no checker is deleted and every target comes back in the failed list",
        )

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
                    f"failed[{i}].id",
                    failure.id,
                    SameAs(
                        checker.id,
                        Says(
                            f"{i + 1}번째로 미리 저장한 검사기",
                            english=f"the checker seeded in advance number {i + 1}",
                        ),
                    ),
                ),
                Held(f"failed[{i}].message", failure.message, Mentions(self.reason)),
            ]
        return verdicts


@dataclass(frozen=True)
class EveryAssignmentIsListed(Then[AssignmentsAndACaller, AssignmentsAnswered]):
    """심은 할당이 모두 한 번씩 집계되고, 각각이 통째로 온다. id 순으로 본다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 할당이 모두 한 번씩 집계되어 전체가 반환됩니다",
            english=(
                "every assignment seeded in advance is counted once and each comes back whole"
            ),
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
        got = sorted(payload.items, key=lambda one: one.id)
        expected = sorted(answer.ids, key=lambda one: one)
        seen: list[Verdict] = [
            Same("items.id", [one.id for one in got], list(expected)),
            Same("total_count", payload.total_count, len(laid.domains)),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]
        by_scope: dict[UUID, DomainData] = {domain.id: domain for domain in laid.domains}
        for i, node in enumerate(got):
            domain = by_scope.get(node.scope_id)
            if domain is None:
                seen.append(
                    Same(
                        f"items[{i}].scope_id",
                        node.scope_id,
                        Says("미리 저장한 도메인", english="a domain seeded in advance"),
                    )
                )
                continue
            seen += [
                Same(f"items[{i}].scope_type", node.scope_type, IdleCheckerScopeTypeDTO.DOMAIN),
                Held[UUID](
                    f"items[{i}].scope_id",
                    node.scope_id,
                    SameAs(
                        domain.id,
                        Says("미리 저장한 도메인", english="the domain seeded in advance"),
                    ),
                ),
                Held[IdleCheckerID](
                    f"items[{i}].idle_checker_id",
                    node.idle_checker_id,
                    SameAs(
                        laid.checker.id,
                        Says("미리 저장한 검사기", english="the checker seeded in advance"),
                    ),
                ),
                Same(f"items[{i}].enabled", node.enabled, True),
                Held(f"items[{i}].created_at", node.created_at, written),
                Held(f"items[{i}].updated_at", node.updated_at, written),
            ]
        return seen


@dataclass(frozen=True)
class EveryAssignmentComesBack(Then[AssignmentsAndACaller, PartialBulkAnswered]):
    """요청한 할당이 모두 처리된 목록에 온다. `missing`이 있으면 그 id 만 실패 목록에 온다."""

    started: datetime
    enabled: bool
    missing: UUID | None = None

    @override
    def says(self) -> str:
        state = "활성" if self.enabled else "비활성"
        state_en = "enabled" if self.enabled else "disabled"
        if self.missing is None:
            return Says(
                f"요청한 할당이 모두 {state} 상태로 오고, 실패한 것은 없습니다",
                english=f"every requested assignment comes back {state_en} and nothing failed",
            )
        return Says(
            f"요청한 할당이 모두 {state} 상태로 오고, 없는 id 는 대상이 없다는 이유로 "
            "실패 목록에 옵니다",
            english=(
                f"every requested assignment comes back {state_en} and an unknown id comes back "
                "in the failed list because no target answers to it"
            ),
        )

    @override
    def look(
        self, laid: AssignmentsAndACaller, answered: Answered[PartialBulkAnswered]
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
                    SameAs(
                        answer.ids[i],
                        Says(
                            f"요청에 넣은 {i + 1}번째 id",
                            english=f"the id put in the request number {i + 1}",
                        ),
                    ),
                ),
                Same(f"successes[{i}].scope_type", node.scope_type, IdleCheckerScopeTypeDTO.DOMAIN),
                Held[UUID](
                    f"successes[{i}].scope_id",
                    node.scope_id,
                    SameAs(
                        domain.id,
                        Says(
                            f"{i + 1}번째로 미리 저장한 도메인",
                            english=f"the domain seeded in advance number {i + 1}",
                        ),
                    ),
                ),
                Held[IdleCheckerID](
                    f"successes[{i}].idle_checker_id",
                    node.idle_checker_id,
                    SameAs(
                        laid.checker.id,
                        Says("미리 저장한 검사기", english="the checker seeded in advance"),
                    ),
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
                Held[UUID](
                    "failed[0].id",
                    failure.id,
                    SameAs(
                        self.missing,
                        Says("요청에 넣은 없는 id", english="the unknown id put in the request"),
                    ),
                ),
                Held(
                    "failed[0].message",
                    failure.message,
                    Mentions("No such idle checker assignment"),
                ),
            ]
        return verdicts


@dataclass(frozen=True)
class NoAssignmentIsProcessed(Then[AssignmentsAndACaller, PartialBulkAnswered]):
    """처리된 할당 없이, 요청한 할당이 모두 같은 이유로 실패 목록에 온다."""

    reason: str

    @override
    def says(self) -> str:
        return Says(
            "처리된 할당 없이 요청한 할당이 모두 실패 목록에 옵니다",
            english=(
                "no assignment is processed and every requested assignment comes back in the "
                "failed list"
            ),
        )

    @override
    def look(
        self, laid: AssignmentsAndACaller, answered: Answered[PartialBulkAnswered]
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
                    SameAs(
                        answer.ids[i],
                        Says(
                            f"요청에 넣은 {i + 1}번째 id",
                            english=f"the id put in the request number {i + 1}",
                        ),
                    ),
                ),
                Held(f"failed[{i}].message", failure.message, Mentions(self.reason)),
            ]
        return verdicts
