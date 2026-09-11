"""What an audit-log scenario table says besides the call.

A record is a field of whatever entity it is about, laid under that entity, so a table
needs the entities, the records on them, and the reader granted on one of them. The three
reads share their answer shape — a page of records — so the situations differ only in what
was laid and who is asking.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import UUID, uuid4

from bai_scenario.components.domain import WAS_HERE, SomeoneOf
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.seeds.audit_log.audit_log import SeedAuditRecord
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.project.project import SeedProject
from bai_scenario.seeds.rbac.role import SeedPermission, SeedRole
from bai_scenario.seeds.resource_policy.project import SeedProjectPolicy
from bai_scenario.seeds.seeder import Laid

from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.audit_log.response import AuditLogNode, SearchAuditLogsPayload
from ai.backend.manager.actions.types import OperationStatus
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.user.types import UserData
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Same,
    Then,
    Verdict,
)

# Two clearly ordered timestamps, so a "newest first" answer is a fixed order rather than
# whatever the clock did during the run. No assertion compares a record's created_at
# against the run window, so the values need not be recent.
EARLY = datetime(2026, 1, 1, tzinfo=UTC)
LATE = datetime(2026, 1, 2, tzinfo=UTC)

# The operation each record carries — the field a scenario reads a record back by, since
# its id is made by the database.
OP_LATE = "edited"
OP_EARLY = "created"
OP_OK = "succeeded"
OP_DENIED = "was-refused"
OP_MINE = "acted-by-me"
OP_THEIRS = "acted-by-another"


@dataclass(frozen=True)
class RecordsAndACaller:
    """Records that exist and the person asking. ``visible_ops`` is the answer expected,
    newest first; ``filter_triggered`` is the actor a filtering read narrows to."""

    caller: UserData
    visible_ops: tuple[str, ...]
    filter_triggered: UUID | None = None


@dataclass(frozen=True)
class RecordsToLoad:
    """Two records to name by id, and the person asking."""

    caller: UserData
    first: tuple[UUID, str]
    second: tuple[UUID, str]


@dataclass(frozen=True)
class ScopedEntities:
    """The entity ids a scoped read names, and the answer expected of it."""

    caller: UserData
    named: tuple[UUID, ...]
    visible_ops: tuple[str, ...]


@dataclass(frozen=True)
class ScopedActors:
    """The actor user ids a scoped read names, and the answer expected of it."""

    caller: UserData
    named: tuple[UUID, ...]
    visible_ops: tuple[str, ...]


async def grant_reading(
    seeding: SeedingSession,
    entity: Laid[Any],
    to: Laid[UserData],
    *,
    entity_type: EntityType,
    scope_of: Callable[[Any], EntityIdentifier],
) -> None:
    """Give ``to`` READ on ``entity`` through a role in that entity's own scope: the role,
    the READ permission on the entity's type, and the grant."""
    role = await seeding.creating_from(SeedRole(scope_of, name_hint="record-reader"), entity)
    await seeding.adding(SeedPermission(entity_type=entity_type, permission=Permission.READ), role)
    await seeding.granting(role, to, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))


async def lay_two_projects(
    seeding: SeedingSession,
    *,
    grant_first: bool = False,
    grant_second: bool = False,
    role: UserRole = UserRole.USER,
) -> tuple[UserData, UUID, UUID]:
    """A domain with two projects, one record on each, and a caller granted READ on the
    projects asked for. The first project's record is the newer one."""
    domain: Laid[DomainData] = await seeding.creating(
        SeedDomain(name_hint="home", description=WAS_HERE)
    )
    policy = await seeding.once(SeedProjectPolicy())
    first = await seeding.creating_from_two(SeedProject(name_hint="team"), domain, policy)
    second = await seeding.creating_from_two(SeedProject(name_hint="other"), domain, policy)
    await seeding.adding(
        SeedAuditRecord(owner_of=lambda p: ProjectID(p.id), operation=OP_LATE, created_at=LATE),
        first,
    )
    await seeding.adding(
        SeedAuditRecord(owner_of=lambda p: ProjectID(p.id), operation=OP_EARLY, created_at=EARLY),
        second,
    )
    caller = await seeding.within(SomeoneOf(domain, role=role))
    if grant_first:
        await grant_reading(
            seeding,
            first,
            caller,
            entity_type=ProjectEntityType(),
            scope_of=lambda p: ProjectID(p.id),
        )
    if grant_second:
        await grant_reading(
            seeding,
            second,
            caller,
            entity_type=ProjectEntityType(),
            scope_of=lambda p: ProjectID(p.id),
        )
    return (
        seeding.made(caller),
        seeding.made(first).id,
        seeding.made(second).id,
    )


async def lay_two_actors(
    seeding: SeedingSession,
    *,
    caller_is_first: bool = False,
    grant_first_to_caller: bool = False,
) -> tuple[UserData, UUID, UUID]:
    """A domain with two users who each triggered a record, and a caller. The caller is
    the first user, or a third person granted READ on the first user."""
    domain: Laid[DomainData] = await seeding.creating(
        SeedDomain(name_hint="home", description=WAS_HERE)
    )
    first = await seeding.within(SomeoneOf(domain))
    second = await seeding.within(SomeoneOf(domain))
    first_id = seeding.made(first).id
    second_id = seeding.made(second).id
    await seeding.adding(
        SeedAuditRecord(
            owner_of=lambda u: UserID(u.id),
            operation=OP_MINE,
            created_at=LATE,
            triggered_by=UserID(first_id),
        ),
        first,
    )
    await seeding.adding(
        SeedAuditRecord(
            owner_of=lambda u: UserID(u.id),
            operation=OP_THEIRS,
            created_at=EARLY,
            triggered_by=UserID(second_id),
        ),
        second,
    )
    caller = first if caller_is_first else await seeding.within(SomeoneOf(domain))
    if grant_first_to_caller:
        await grant_reading(
            seeding, first, caller, entity_type=UserEntityType(), scope_of=lambda u: UserID(u.id)
        )
    return seeding.made(caller), first_id, second_id


@dataclass(frozen=True)
class TwoRecordsGlobally(Given[Any, RecordsAndACaller]):
    """Two records that exist, and a caller of the given role. The newer one is first."""

    role: UserRole = UserRole.SUPERADMIN

    @override
    def describe(self) -> str:
        return f"서로 다른 시각의 기록 둘과, {self.role.value} 한 명"

    @override
    async def lay(self, seeding: SeedingSession) -> RecordsAndACaller:
        domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(SomeoneOf(domain, role=self.role))
        await seeding.adding(
            SeedAuditRecord(owner_of=lambda u: UserID(u.id), operation=OP_LATE, created_at=LATE),
            caller,
        )
        await seeding.adding(
            SeedAuditRecord(owner_of=lambda u: UserID(u.id), operation=OP_EARLY, created_at=EARLY),
            caller,
        )
        return RecordsAndACaller(seeding.made(caller), (OP_LATE, OP_EARLY))


@dataclass(frozen=True)
class MixedStatusGlobally(Given[Any, RecordsAndACaller]):
    """A successful record and a denied one, with a superadmin caller."""

    @override
    def describe(self) -> str:
        return "성공한 기록과 거부된 기록, 그리고 슈퍼관리자 한 명"

    @override
    async def lay(self, seeding: SeedingSession) -> RecordsAndACaller:
        domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(SomeoneOf(domain, role=UserRole.SUPERADMIN))
        await seeding.adding(
            SeedAuditRecord(owner_of=lambda u: UserID(u.id), operation=OP_OK, created_at=LATE),
            caller,
        )
        await seeding.adding(
            SeedAuditRecord(
                owner_of=lambda u: UserID(u.id),
                operation=OP_DENIED,
                created_at=EARLY,
                status=OperationStatus.DENIED,
            ),
            caller,
        )
        return RecordsAndACaller(seeding.made(caller), (OP_OK,))


@dataclass(frozen=True)
class TwoActorsGlobally(Given[Any, RecordsAndACaller]):
    """Two users who each triggered a record, and a superadmin caller narrowing to the
    first actor."""

    @override
    def describe(self) -> str:
        return "두 사용자가 각각 남긴 기록과, 슈퍼관리자 한 명"

    @override
    async def lay(self, seeding: SeedingSession) -> RecordsAndACaller:
        domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        first = await seeding.within(SomeoneOf(domain))
        second = await seeding.within(SomeoneOf(domain))
        first_id = seeding.made(first).id
        await seeding.adding(
            SeedAuditRecord(
                owner_of=lambda u: UserID(u.id),
                operation=OP_MINE,
                created_at=LATE,
                triggered_by=UserID(first_id),
            ),
            first,
        )
        await seeding.adding(
            SeedAuditRecord(
                owner_of=lambda u: UserID(u.id),
                operation=OP_THEIRS,
                created_at=EARLY,
                triggered_by=UserID(seeding.made(second).id),
            ),
            second,
        )
        caller = await seeding.within(SomeoneOf(domain, role=UserRole.SUPERADMIN))
        return RecordsAndACaller(seeding.made(caller), (OP_MINE,), filter_triggered=first_id)


@dataclass(frozen=True)
class ManyRecordsGlobally(Given[Any, RecordsAndACaller]):
    """More records than one default page holds, with a superadmin caller."""

    total: int = 11

    @override
    def describe(self) -> str:
        return f"기록 {self.total}개와, 슈퍼관리자 한 명"

    @override
    async def lay(self, seeding: SeedingSession) -> RecordsAndACaller:
        domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(SomeoneOf(domain, role=UserRole.SUPERADMIN))
        for i in range(self.total):
            await seeding.adding(
                SeedAuditRecord(
                    owner_of=lambda u: UserID(u.id), operation=f"op-{i}", created_at=EARLY
                ),
                caller,
            )
        return RecordsAndACaller(seeding.made(caller), ())


@dataclass(frozen=True)
class TwoRecordsToRead(Given[Any, RecordsToLoad]):
    """Two records to name by id, and a caller of the given role."""

    role: UserRole = UserRole.SUPERADMIN

    @override
    def describe(self) -> str:
        return f"id로 집을 기록 둘과, {self.role.value} 한 명"

    @override
    async def lay(self, seeding: SeedingSession) -> RecordsToLoad:
        domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(SomeoneOf(domain, role=self.role))
        first = await seeding.adding(
            SeedAuditRecord(owner_of=lambda u: UserID(u.id), operation=OP_LATE, created_at=LATE),
            caller,
        )
        second = await seeding.adding(
            SeedAuditRecord(owner_of=lambda u: UserID(u.id), operation=OP_EARLY, created_at=EARLY),
            caller,
        )
        return RecordsToLoad(
            seeding.made(caller),
            (seeding.made(first).id, OP_LATE),
            (seeding.made(second).id, OP_EARLY),
        )


@dataclass(frozen=True)
class ProjectRecords(Given[Any, ScopedEntities]):
    """Two projects with a record each, and a caller granted READ on the projects asked
    for. ``name`` says what the request will scope to: the first, both, or an id nothing
    answers to."""

    role: UserRole = UserRole.USER
    grant_first: bool = False
    grant_second: bool = False
    name: str = "first"

    @override
    def describe(self) -> str:
        granted = [n for n, g in (("첫째", self.grant_first), ("둘째", self.grant_second)) if g]
        holding = f"{'·'.join(granted)} 프로젝트에 읽기 권한" if granted else "아무 권한도"
        return f"서로 다른 프로젝트의 기록 둘과, {holding} 받은 {self.role.value} 한 명"

    @override
    async def lay(self, seeding: SeedingSession) -> ScopedEntities:
        caller, first, second = await lay_two_projects(
            seeding,
            grant_first=self.grant_first,
            grant_second=self.grant_second,
            role=self.role,
        )
        match self.name:
            case "both":
                return ScopedEntities(caller, (first, second), (OP_LATE, OP_EARLY))
            case "unknown":
                return ScopedEntities(caller, (uuid4(),), ())
            case _:
                return ScopedEntities(caller, (first,), (OP_LATE,))


@dataclass(frozen=True)
class OneProjectMixedStatus(Given[Any, ScopedEntities]):
    """A single project holding a successful record and a denied one, with a caller
    granted READ on it."""

    @override
    def describe(self) -> str:
        return "성공한 기록과 거부된 기록을 가진 프로젝트 하나와, 읽기 권한을 받은 사용자 한 명"

    @override
    async def lay(self, seeding: SeedingSession) -> ScopedEntities:
        domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        policy = await seeding.once(SeedProjectPolicy())
        project = await seeding.creating_from_two(SeedProject(name_hint="team"), domain, policy)
        await seeding.adding(
            SeedAuditRecord(owner_of=lambda p: ProjectID(p.id), operation=OP_OK, created_at=LATE),
            project,
        )
        await seeding.adding(
            SeedAuditRecord(
                owner_of=lambda p: ProjectID(p.id),
                operation=OP_DENIED,
                created_at=EARLY,
                status=OperationStatus.DENIED,
            ),
            project,
        )
        caller = await seeding.within(SomeoneOf(domain))
        await grant_reading(
            seeding,
            project,
            caller,
            entity_type=ProjectEntityType(),
            scope_of=lambda p: ProjectID(p.id),
        )
        return ScopedEntities(seeding.made(caller), (seeding.made(project).id,), (OP_OK,))


@dataclass(frozen=True)
class OneProjectManyRecords(Given[Any, ScopedEntities]):
    """A single project holding more records than a default page, with a granted caller."""

    total: int = 11

    @override
    def describe(self) -> str:
        return f"기록 {self.total}개를 가진 프로젝트 하나와, 읽기 권한을 받은 사용자 한 명"

    @override
    async def lay(self, seeding: SeedingSession) -> ScopedEntities:
        domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        policy = await seeding.once(SeedProjectPolicy())
        project = await seeding.creating_from_two(SeedProject(name_hint="team"), domain, policy)
        for i in range(self.total):
            await seeding.adding(
                SeedAuditRecord(
                    owner_of=lambda p: ProjectID(p.id), operation=f"op-{i}", created_at=EARLY
                ),
                project,
            )
        caller = await seeding.within(SomeoneOf(domain))
        await grant_reading(
            seeding,
            project,
            caller,
            entity_type=ProjectEntityType(),
            scope_of=lambda p: ProjectID(p.id),
        )
        return ScopedEntities(seeding.made(caller), (seeding.made(project).id,), ())


@dataclass(frozen=True)
class ActorRecords(Given[Any, ScopedActors]):
    """Two users who each triggered a record, and a caller. ``caller_is_first`` makes the
    caller the first actor; ``grant`` gives a separate reader READ on the first user."""

    caller_is_first: bool = False
    grant: bool = False

    @override
    def describe(self) -> str:
        who = (
            "그중 첫 사용자" if self.caller_is_first else "그 사용자에 읽기 권한을 받은 다른 한 명"
        )
        return f"두 사용자가 각각 일으킨 기록과, {who}"

    @override
    async def lay(self, seeding: SeedingSession) -> ScopedActors:
        caller, first_id, _second_id = await lay_two_actors(
            seeding, caller_is_first=self.caller_is_first, grant_first_to_caller=self.grant
        )
        return ScopedActors(caller, (first_id,), (OP_MINE,))


@dataclass(frozen=True)
class TheRecordsAnswered(Then[Any, SearchAuditLogsPayload]):
    """The records named come back, in the order named, and only those.

    A page of records, so the answer is the set found and the counts, not one node
    compared whole.
    """

    @override
    def says(self) -> str:
        return "지목한 기록이 순서대로, 그리고 그것만 온다"

    @override
    def look(self, laid: Any, answered: Answered[SearchAuditLogsPayload]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Same("answer", repr(answered.raised), "a page of records")]
        return [
            Same("items", [one.operation for one in payload.items], list(laid.visible_ops)),
            Same("total_count", payload.total_count, len(laid.visible_ops)),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class ThePageIsCapped(Then[Any, SearchAuditLogsPayload]):
    """The default page comes back capped, and says another page follows."""

    size: int
    total: int

    @override
    def says(self) -> str:
        return "기본 페이지 크기만큼 오고 다음 페이지가 있다고 답한다"

    @override
    def look(self, laid: Any, answered: Answered[SearchAuditLogsPayload]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Same("answer", repr(answered.raised), "a page of records")]
        return [
            Same("items_count", len(payload.items), self.size),
            Same("total_count", payload.total_count, self.total),
            Same("has_next_page", payload.has_next_page, True),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheNodesInOrder(Then[RecordsToLoad, list[AuditLogNode | None]]):
    """Each id gets its node in the order named; an id nothing answers to gets a gap."""

    expected: tuple[str | None, ...]

    @override
    def says(self) -> str:
        return "준 순서대로 오고, 없는 id 자리는 비어 있다"

    @override
    def look(
        self, laid: RecordsToLoad, answered: Answered[list[AuditLogNode | None]]
    ) -> list[Verdict]:
        nodes = answered.response
        if nodes is None:
            return [Same("answer", repr(answered.raised), "a list of nodes")]
        got = [None if node is None else node.operation for node in nodes]
        return [Same("operations", got, list(self.expected))]
