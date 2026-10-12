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

from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.audit_log.response import (
    AuditLogNode,
    SearchAuditLogScopesPayload,
    SearchAuditLogsPayload,
)
from ai.backend.common.dto.manager.v2.audit_log.types import AuditLogStatus
from ai.backend.manager.actions.types import OperationStatus
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Skipped,
    Then,
    Verdict,
)
from bai_scenario.components.domain import WAS_HERE, SomeoneOf
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.seeds.audit_log.audit_log import TestSeedAuditRecord, TestSeedScopedAuditRecord
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.project.project import TestSeedProject
from bai_scenario.seeds.rbac.role import TestSeedPermission, TestSeedRole
from bai_scenario.seeds.resource_policy.project import TestSeedProjectPolicy
from bai_scenario.seeds.seeder import Laid

# Two clearly ordered timestamps, so a "newest first" answer is a fixed order rather than
# whatever the clock did during the run.
EARLY = datetime(2026, 1, 1, tzinfo=UTC)
LATE = datetime(2026, 1, 2, tzinfo=UTC)

# The operation each record carries — a field a scenario can name and compare, since the
# id is made by the database.
OP_LATE = "edited"
OP_EARLY = "created"
OP_OK = "succeeded"
OP_DENIED = "was-refused"
OP_MINE = "acted-by-me"
OP_THEIRS = "acted-by-another"
OP_SCOPED = "linked"
OP_TRIGGERED = "acted-on-a-project"


@dataclass(frozen=True)
class ExpectedRecord:
    """The whole of one record's answer, save the ids the database and each run make.

    ``entity_id`` and ``triggered_by`` are ids earlier steps made, compared as coming from
    those rows rather than by value; the rest is fixed by the seed.
    """

    operation: str
    entity_type: str
    entity_id: UUID
    created_at: datetime
    status: AuditLogStatus = AuditLogStatus.SUCCESS
    triggered_by: UUID | None = None


def look_node(node: AuditLogNode, expected: ExpectedRecord, *, at: str = "") -> list[Verdict]:
    """The whole node, checked. The ids the database and the run make are skipped; the
    owner and actor are read as coming from the rows earlier steps laid."""
    verdicts: list[Verdict] = [
        Skipped(f"{at}id", "데이터베이스가 만든다"),
        Skipped(f"{at}action_id", "실행마다 새로 생성된다"),
        Same(f"{at}operation", node.operation, expected.operation),
        Same(f"{at}entity_type", node.entity_type, expected.entity_type),
        Held(
            f"{at}entity_id",
            node.entity_id,
            SameAs[str | None](str(expected.entity_id), "기록의 대상 엔티티"),
        ),
        Held(
            f"{at}target_entity_id",
            node.target_entity_id,
            SameAs[UUID | None](expected.entity_id, "기록의 대상 엔티티"),
        ),
        Same(f"{at}status", node.status, expected.status),
        Same(f"{at}description", node.description, f"{expected.operation} was recorded"),
        Same(f"{at}created_at", node.created_at, expected.created_at),
        Same(f"{at}request_id", node.request_id, None),
        Same(f"{at}acted_as", node.acted_as, None),
        Same(f"{at}duration", node.duration, None),
        Same(f"{at}client_ip", node.client_ip, None),
    ]
    if expected.triggered_by is None:
        verdicts.append(Same(f"{at}triggered_by", node.triggered_by, None))
    else:
        verdicts.append(
            Held(
                f"{at}triggered_by",
                node.triggered_by,
                SameAs[str | None](str(expected.triggered_by), "실행한 사용자"),
            )
        )
    return verdicts


@dataclass(frozen=True)
class RecordsAndACaller:
    """Records that exist and the person asking. ``visible`` is the answer expected,
    newest first; ``filter_triggered`` is the actor a filtering read narrows to."""

    caller: UserData
    visible: tuple[ExpectedRecord, ...]
    filter_triggered: UUID | None = None


@dataclass(frozen=True)
class RecordsToLoad:
    """Two records to name by id, and the person asking. Each pairs the id to name with
    the node expected back."""

    caller: UserData
    first: tuple[UUID, ExpectedRecord]
    second: tuple[UUID, ExpectedRecord]


@dataclass(frozen=True)
class ScopedEntities:
    """The entity ids a scoped read names, and the answer expected of it."""

    caller: UserData
    named: tuple[UUID, ...]
    visible: tuple[ExpectedRecord, ...]


@dataclass(frozen=True)
class ScopedActors:
    """The actor user ids a scoped read names, and the answer expected of it."""

    caller: UserData
    named: tuple[UUID, ...]
    visible: tuple[ExpectedRecord, ...]


async def grant_reading(
    seeding: TestSeedingSession,
    entity: Laid[Any],
    to: Laid[UserData],
    *,
    entity_type: EntityType,
    scope_of: Callable[[Any], EntityIdentifier],
) -> None:
    """Give ``to`` READ on ``entity`` through a role in that entity's own scope: the role,
    the READ permission on the entity's type, and the grant."""
    role = await seeding.creating_from(TestSeedRole(scope_of, name_hint="record-reader"), entity)
    await seeding.adding(
        TestSeedPermission(entity_type=entity_type, permission=Permission.READ), role
    )
    await seeding.granting(role, to, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))


@dataclass(frozen=True)
class TwoProjectsLaid:
    """Two projects with a record each, and the caller. The first project's record is
    the newer one."""

    caller: UserData
    first_project: UUID
    second_project: UUID
    first_record: UUID
    second_record: UUID


async def lay_two_projects(
    seeding: TestSeedingSession,
    *,
    grant_first: bool = False,
    grant_second: bool = False,
    role: UserRole = UserRole.USER,
) -> TwoProjectsLaid:
    """A domain with two projects, one record on each, and a caller granted READ on the
    projects asked for."""
    domain: Laid[DomainData] = await seeding.creating(
        TestSeedDomain(name_hint="home", description=WAS_HERE)
    )
    policy = await seeding.once(TestSeedProjectPolicy())
    first = await seeding.creating_from_two(TestSeedProject(name_hint="team"), domain, policy)
    second = await seeding.creating_from_two(TestSeedProject(name_hint="other"), domain, policy)
    first_record = await seeding.adding(
        TestSeedAuditRecord(owner_of=lambda p: ProjectID(p.id), operation=OP_LATE, created_at=LATE),
        first,
    )
    second_record = await seeding.adding(
        TestSeedAuditRecord(
            owner_of=lambda p: ProjectID(p.id), operation=OP_EARLY, created_at=EARLY
        ),
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
    return TwoProjectsLaid(
        seeding.made(caller),
        seeding.made(first).id,
        seeding.made(second).id,
        seeding.made(first_record).id,
        seeding.made(second_record).id,
    )


async def lay_two_actors(
    seeding: TestSeedingSession,
    *,
    caller_is_first: bool = False,
    grant_first_to_caller: bool = False,
) -> tuple[UserData, UUID, UUID]:
    """A domain with two users who each triggered a record, and a caller. The caller is
    the first user, or a third person granted READ on the first user."""
    domain: Laid[DomainData] = await seeding.creating(
        TestSeedDomain(name_hint="home", description=WAS_HERE)
    )
    first = await seeding.within(SomeoneOf(domain))
    second = await seeding.within(SomeoneOf(domain))
    first_id = seeding.made(first).id
    second_id = seeding.made(second).id
    await seeding.adding(
        TestSeedAuditRecord(
            owner_of=lambda u: UserID(u.id),
            operation=OP_MINE,
            created_at=LATE,
            triggered_by=UserID(first_id),
        ),
        first,
    )
    await seeding.adding(
        TestSeedAuditRecord(
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
    async def lay(self, seeding: TestSeedingSession) -> RecordsAndACaller:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(SomeoneOf(domain, role=self.role))
        await seeding.adding(
            TestSeedAuditRecord(
                owner_of=lambda u: UserID(u.id), operation=OP_LATE, created_at=LATE
            ),
            caller,
        )
        await seeding.adding(
            TestSeedAuditRecord(
                owner_of=lambda u: UserID(u.id), operation=OP_EARLY, created_at=EARLY
            ),
            caller,
        )
        made = seeding.made(caller)
        return RecordsAndACaller(
            made,
            (
                ExpectedRecord(OP_LATE, "user", made.id, LATE),
                ExpectedRecord(OP_EARLY, "user", made.id, EARLY),
            ),
        )


@dataclass(frozen=True)
class MixedStatusGlobally(Given[Any, RecordsAndACaller]):
    """A successful record and a denied one, with a superadmin caller."""

    @override
    def describe(self) -> str:
        return "성공한 기록과 거부된 기록, 그리고 슈퍼관리자 한 명"

    @override
    async def lay(self, seeding: TestSeedingSession) -> RecordsAndACaller:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(SomeoneOf(domain, role=UserRole.SUPERADMIN))
        await seeding.adding(
            TestSeedAuditRecord(owner_of=lambda u: UserID(u.id), operation=OP_OK, created_at=LATE),
            caller,
        )
        await seeding.adding(
            TestSeedAuditRecord(
                owner_of=lambda u: UserID(u.id),
                operation=OP_DENIED,
                created_at=EARLY,
                status=OperationStatus.DENIED,
            ),
            caller,
        )
        made = seeding.made(caller)
        return RecordsAndACaller(made, (ExpectedRecord(OP_OK, "user", made.id, LATE),))


@dataclass(frozen=True)
class TwoActorsGlobally(Given[Any, RecordsAndACaller]):
    """Two users who each triggered a record, and a superadmin caller narrowing to the
    first actor."""

    @override
    def describe(self) -> str:
        return "두 사용자가 각각 남긴 기록과, 슈퍼관리자 한 명"

    @override
    async def lay(self, seeding: TestSeedingSession) -> RecordsAndACaller:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        first = await seeding.within(SomeoneOf(domain))
        second = await seeding.within(SomeoneOf(domain))
        first_id = seeding.made(first).id
        await seeding.adding(
            TestSeedAuditRecord(
                owner_of=lambda u: UserID(u.id),
                operation=OP_MINE,
                created_at=LATE,
                triggered_by=UserID(first_id),
            ),
            first,
        )
        await seeding.adding(
            TestSeedAuditRecord(
                owner_of=lambda u: UserID(u.id),
                operation=OP_THEIRS,
                created_at=EARLY,
                triggered_by=UserID(seeding.made(second).id),
            ),
            second,
        )
        caller = await seeding.within(SomeoneOf(domain, role=UserRole.SUPERADMIN))
        return RecordsAndACaller(
            seeding.made(caller),
            (ExpectedRecord(OP_MINE, "user", first_id, LATE, triggered_by=first_id),),
            filter_triggered=first_id,
        )


@dataclass(frozen=True)
class ManyRecordsGlobally(Given[Any, RecordsAndACaller]):
    """More records than one default page holds, with a superadmin caller."""

    total: int = 11

    @override
    def describe(self) -> str:
        return f"기록 {self.total}개와, 슈퍼관리자 한 명"

    @override
    async def lay(self, seeding: TestSeedingSession) -> RecordsAndACaller:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(SomeoneOf(domain, role=UserRole.SUPERADMIN))
        for i in range(self.total):
            await seeding.adding(
                TestSeedAuditRecord(
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
        return f"id로 조회할 자기에 대한 기록 둘과, {self.role.value} 한 명"

    @override
    async def lay(self, seeding: TestSeedingSession) -> RecordsToLoad:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(SomeoneOf(domain, role=self.role))
        first = await seeding.adding(
            TestSeedAuditRecord(
                owner_of=lambda u: UserID(u.id), operation=OP_LATE, created_at=LATE
            ),
            caller,
        )
        second = await seeding.adding(
            TestSeedAuditRecord(
                owner_of=lambda u: UserID(u.id), operation=OP_EARLY, created_at=EARLY
            ),
            caller,
        )
        made = seeding.made(caller)
        return RecordsToLoad(
            made,
            (seeding.made(first).id, ExpectedRecord(OP_LATE, "user", made.id, LATE)),
            (seeding.made(second).id, ExpectedRecord(OP_EARLY, "user", made.id, EARLY)),
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
        holding = (
            f"{'·'.join(granted)} 프로젝트에 읽기 권한을 받은" if granted else "아무 권한도 없는"
        )
        return f"서로 다른 프로젝트의 기록 둘과, {holding} {self.role.value} 한 명"

    @override
    async def lay(self, seeding: TestSeedingSession) -> ScopedEntities:
        laid = await lay_two_projects(
            seeding,
            grant_first=self.grant_first,
            grant_second=self.grant_second,
            role=self.role,
        )
        first, second = laid.first_project, laid.second_project
        match self.name:
            case "both":
                return ScopedEntities(
                    laid.caller,
                    (first, second),
                    (
                        ExpectedRecord(OP_LATE, "project", first, LATE),
                        ExpectedRecord(OP_EARLY, "project", second, EARLY),
                    ),
                )
            case "unknown":
                return ScopedEntities(laid.caller, (uuid4(),), ())
            case _:
                return ScopedEntities(
                    laid.caller, (first,), (ExpectedRecord(OP_LATE, "project", first, LATE),)
                )


@dataclass(frozen=True)
class ProjectRecordsToLoad(Given[Any, RecordsToLoad]):
    """Two projects with a record each, and a caller granted READ on the first project
    only. The first record is the one the caller may read."""

    @override
    def describe(self) -> str:
        return "서로 다른 프로젝트의 기록 둘과, 첫째 프로젝트에만 읽기 권한을 받은 사용자 한 명"

    @override
    async def lay(self, seeding: TestSeedingSession) -> RecordsToLoad:
        laid = await lay_two_projects(seeding, grant_first=True)
        return RecordsToLoad(
            laid.caller,
            (laid.first_record, ExpectedRecord(OP_LATE, "project", laid.first_project, LATE)),
            (laid.second_record, ExpectedRecord(OP_EARLY, "project", laid.second_project, EARLY)),
        )


@dataclass(frozen=True)
class OneProjectMixedStatus(Given[Any, ScopedEntities]):
    """A single project holding a successful record and a denied one, with a caller
    granted READ on it."""

    @override
    def describe(self) -> str:
        return "성공한 기록과 거부된 기록을 가진 프로젝트 하나와, 읽기 권한을 받은 사용자 한 명"

    @override
    async def lay(self, seeding: TestSeedingSession) -> ScopedEntities:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        policy = await seeding.once(TestSeedProjectPolicy())
        project = await seeding.creating_from_two(TestSeedProject(name_hint="team"), domain, policy)
        await seeding.adding(
            TestSeedAuditRecord(
                owner_of=lambda p: ProjectID(p.id), operation=OP_OK, created_at=LATE
            ),
            project,
        )
        await seeding.adding(
            TestSeedAuditRecord(
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
        pid = seeding.made(project).id
        return ScopedEntities(
            seeding.made(caller), (pid,), (ExpectedRecord(OP_OK, "project", pid, LATE),)
        )


@dataclass(frozen=True)
class OneProjectManyRecords(Given[Any, ScopedEntities]):
    """A single project holding more records than a default page, with a granted caller."""

    total: int = 11

    @override
    def describe(self) -> str:
        return f"기록 {self.total}개를 가진 프로젝트 하나와, 읽기 권한을 받은 사용자 한 명"

    @override
    async def lay(self, seeding: TestSeedingSession) -> ScopedEntities:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        policy = await seeding.once(TestSeedProjectPolicy())
        project = await seeding.creating_from_two(TestSeedProject(name_hint="team"), domain, policy)
        for i in range(self.total):
            await seeding.adding(
                TestSeedAuditRecord(
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
class ARecordScopedToAProject(Given[Any, ScopedEntities]):
    """A record about a user, tagged with a project scope, and a caller granted READ on
    that project. The record's own entity is not the project, so only the scope tag makes
    a search by the project find it."""

    @override
    def describe(self) -> str:
        return (
            "다른 엔티티에 대한 기록이 한 프로젝트를 스코프로 달고 있고, 그 프로젝트에 읽기 "
            "권한을 받은 사용자 한 명"
        )

    @override
    async def lay(self, seeding: TestSeedingSession) -> ScopedEntities:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        policy = await seeding.once(TestSeedProjectPolicy())
        project = await seeding.creating_from_two(TestSeedProject(name_hint="team"), domain, policy)
        subject = await seeding.within(SomeoneOf(domain))
        pid = seeding.made(project).id
        await seeding.adding_with_nested(
            TestSeedScopedAuditRecord(
                owner_of=lambda u: UserID(u.id),
                operation=OP_SCOPED,
                created_at=LATE,
                scopes=((ProjectEntityType(), pid),),
            ),
            subject,
        )
        caller = await seeding.within(SomeoneOf(domain))
        await grant_reading(
            seeding,
            project,
            caller,
            entity_type=ProjectEntityType(),
            scope_of=lambda p: ProjectID(p.id),
        )
        return ScopedEntities(
            seeding.made(caller),
            (pid,),
            (ExpectedRecord(OP_SCOPED, "user", seeding.made(subject).id, LATE),),
        )


@dataclass(frozen=True)
class ActorRecords(Given[Any, ScopedActors]):
    """Two users who each triggered a record, and a caller. ``caller_is_first`` makes the
    caller the first actor; ``grant`` gives a separate reader READ on the first user."""

    caller_is_first: bool = False
    grant: bool = False

    @override
    def describe(self) -> str:
        who = (
            "그중 첫 사용자"
            if self.caller_is_first
            else "그 사용자에 대한 읽기 권한을 받은 다른 사용자 한 명"
        )
        return f"두 사용자가 각각 실행한 기록과, {who}"

    @override
    async def lay(self, seeding: TestSeedingSession) -> ScopedActors:
        caller, first_id, _second_id = await lay_two_actors(
            seeding, caller_is_first=self.caller_is_first, grant_first_to_caller=self.grant
        )
        return ScopedActors(
            caller,
            (first_id,),
            (ExpectedRecord(OP_MINE, "user", first_id, LATE, triggered_by=first_id),),
        )


@dataclass(frozen=True)
class TheRecordsAnswered(Then[Any, SearchAuditLogsPayload]):
    """The records expected come back, in order and whole, and only those.

    Each item is checked field by field against what was laid; a page carries the counts
    the run promises besides.
    """

    @override
    def says(self) -> str:
        return "지정한 기록이 순서대로, 그리고 그것만 반환된다"

    @override
    def look(self, laid: Any, answered: Answered[SearchAuditLogsPayload]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Same("answer", repr(answered.raised), "a page of records")]
        verdicts: list[Verdict] = [
            Same("item_count", len(payload.items), len(laid.visible)),
            Same("total_count", payload.total_count, len(laid.visible)),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]
        for node, expected in zip(payload.items, laid.visible, strict=False):
            verdicts.extend(look_node(node, expected))
        return verdicts


@dataclass(frozen=True)
class ThePageIsCapped(Then[Any, SearchAuditLogsPayload]):
    """The default page comes back capped, and says another page follows."""

    size: int
    total: int

    @override
    def says(self) -> str:
        return "기본 페이지 크기만큼 반환되고 다음 페이지가 있다고 응답한다"

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


type Loaded = list[AuditLogNode | Exception | None]


@dataclass(frozen=True)
class TheSlotsInOrder(Then[RecordsToLoad, Loaded]):
    """Each id is answered in the order named: its node whole, a refusal, or a gap for an
    id nothing answers to. A slot names which — ``first``, ``second``, ``refused``, ``gap``."""

    slots: tuple[str, ...]

    @override
    def says(self) -> str:
        return "요청한 순서대로 항목마다 노드, 거부, 또는 빈 항목이 반환된다"

    @override
    def look(self, laid: RecordsToLoad, answered: Answered[Loaded]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [Same("answer", repr(answered.raised), "a list of nodes")]
        by = {"first": laid.first[1], "second": laid.second[1]}
        verdicts: list[Verdict] = [Same("length", len(loaded), len(self.slots))]
        for index, (got, slot) in enumerate(zip(loaded, self.slots, strict=False)):
            match slot:
                case "gap":
                    verdicts.append(Same(f"[{index}]", got, None))
                case "refused":
                    verdicts.append(
                        Refused(NotEnoughPermission, got if isinstance(got, Exception) else None)
                    )
                case _:
                    verdicts.extend(
                        look_node(got, by[slot], at=f"[{index}].")
                        if isinstance(got, AuditLogNode)
                        else [Same(f"[{index}]", type(got).__name__, "AuditLogNode")]
                    )
        return verdicts


@dataclass(frozen=True)
class ARecordReachedThroughItsScope(Given[Any, RecordsToLoad]):
    """A record about one user, tagged with a project scope, and a record on another
    project. The caller holds READ on the scope project alone, so the first record is
    reached through its scope and the second not at all."""

    @override
    def describe(self) -> str:
        return (
            "한 사용자에 대한 기록이 한 프로젝트를 범위로 남겼고, 다른 프로젝트에 기록 하나가 "
            "있으며, 범위 프로젝트에만 읽기 권한을 받은 사용자 한 명"
        )

    @override
    async def lay(self, seeding: TestSeedingSession) -> RecordsToLoad:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        policy = await seeding.once(TestSeedProjectPolicy())
        scope = await seeding.creating_from_two(TestSeedProject(name_hint="team"), domain, policy)
        other = await seeding.creating_from_two(TestSeedProject(name_hint="other"), domain, policy)
        subject = await seeding.within(SomeoneOf(domain))
        scoped = await seeding.adding_with_nested(
            TestSeedScopedAuditRecord(
                owner_of=lambda u: UserID(u.id),
                operation=OP_SCOPED,
                created_at=LATE,
                scopes=((ProjectEntityType(), seeding.made(scope).id),),
            ),
            subject,
        )
        unreachable = await seeding.adding(
            TestSeedAuditRecord(
                owner_of=lambda p: ProjectID(p.id), operation=OP_EARLY, created_at=EARLY
            ),
            other,
        )
        caller = await seeding.within(SomeoneOf(domain))
        await grant_reading(
            seeding,
            scope,
            caller,
            entity_type=ProjectEntityType(),
            scope_of=lambda p: ProjectID(p.id),
        )
        return RecordsToLoad(
            seeding.made(caller),
            (
                seeding.made(scoped).id,
                ExpectedRecord(OP_SCOPED, "user", seeding.made(subject).id, LATE),
            ),
            (
                seeding.made(unreachable).id,
                ExpectedRecord(OP_EARLY, "project", seeding.made(other).id, EARLY),
            ),
        )


@dataclass(frozen=True)
class ARecordReachedThroughItsTrigger(Given[Any, RecordsToLoad]):
    """A record about one project triggered by a user, and a record on another project.
    The caller holds READ on the triggering user alone, so the first record is reached
    through who triggered it and the second not at all."""

    @override
    def describe(self) -> str:
        return (
            "한 프로젝트에 대한 기록을 다른 사용자가 실행했고, 다른 프로젝트에 기록 하나가 "
            "있으며, 실행한 사용자에만 읽기 권한을 받은 사용자 한 명"
        )

    @override
    async def lay(self, seeding: TestSeedingSession) -> RecordsToLoad:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        policy = await seeding.once(TestSeedProjectPolicy())
        about = await seeding.creating_from_two(TestSeedProject(name_hint="team"), domain, policy)
        other = await seeding.creating_from_two(TestSeedProject(name_hint="other"), domain, policy)
        trigger = await seeding.within(SomeoneOf(domain))
        trigger_id = seeding.made(trigger).id
        triggered = await seeding.adding(
            TestSeedAuditRecord(
                owner_of=lambda p: ProjectID(p.id),
                operation=OP_TRIGGERED,
                created_at=LATE,
                triggered_by=UserID(trigger_id),
            ),
            about,
        )
        unreachable = await seeding.adding(
            TestSeedAuditRecord(
                owner_of=lambda p: ProjectID(p.id), operation=OP_EARLY, created_at=EARLY
            ),
            other,
        )
        caller = await seeding.within(SomeoneOf(domain))
        await grant_reading(
            seeding, trigger, caller, entity_type=UserEntityType(), scope_of=lambda u: UserID(u.id)
        )
        return RecordsToLoad(
            seeding.made(caller),
            (
                seeding.made(triggered).id,
                ExpectedRecord(
                    OP_TRIGGERED,
                    "project",
                    seeding.made(about).id,
                    LATE,
                    triggered_by=trigger_id,
                ),
            ),
            (
                seeding.made(unreachable).id,
                ExpectedRecord(OP_EARLY, "project", seeding.made(other).id, EARLY),
            ),
        )


@dataclass(frozen=True)
class ExpectedScope:
    """One scope a record recorded, as the search answers it."""

    scope_type: str
    scope_id: UUID


@dataclass(frozen=True)
class ScopesToSearch:
    """One record whose scopes are searched, the scopes expected back in order, and the
    person asking. ``narrow_id`` is the scope a filtering search narrows to."""

    caller: UserData
    record: UUID
    visible: tuple[ExpectedScope, ...]
    narrow_id: UUID | None = None


@dataclass(frozen=True)
class AScopedRecord(Given[Any, ScopesToSearch]):
    """A record about one project, triggered by a user, that recorded another project and
    a user as its scopes, and a caller who reaches it one way or none.

    ``reader`` says how: ``superadmin``, ``scope`` (READ on the scope project), ``about``
    (READ on the project the record is about), ``trigger`` (READ on the triggering user),
    ``nobody`` or ``monitor`` (no grant). ``narrow`` says which scopes the answer keeps:
    ``all``, ``project`` (by type) or ``user`` (by id).
    """

    reader: str = "superadmin"
    narrow: str = "all"

    @override
    def describe(self) -> str:
        who = {
            "superadmin": "슈퍼관리자 한 명",
            "scope": "범위 프로젝트에만 읽기 권한을 받은 사용자 한 명",
            "about": "대상 프로젝트에만 읽기 권한을 받은 사용자 한 명",
            "trigger": "실행한 사용자에만 읽기 권한을 받은 사용자 한 명",
            "nobody": "아무 권한도 없는 사용자 한 명",
            "monitor": "아무 권한도 없는 모니터 역할 사용자 한 명",
        }[self.reader]
        return (
            "한 프로젝트에 대한 기록을 다른 사용자가 실행했고 그 기록이 다른 프로젝트와 "
            f"한 사용자를 범위로 남겼으며, {who}"
        )

    @override
    async def lay(self, seeding: TestSeedingSession) -> ScopesToSearch:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        policy = await seeding.once(TestSeedProjectPolicy())
        about = await seeding.creating_from_two(TestSeedProject(name_hint="team"), domain, policy)
        scope = await seeding.creating_from_two(TestSeedProject(name_hint="other"), domain, policy)
        member = await seeding.within(SomeoneOf(domain))
        trigger = await seeding.within(SomeoneOf(domain))
        scope_id = seeding.made(scope).id
        member_id = seeding.made(member).id
        record = await seeding.adding_with_nested(
            TestSeedScopedAuditRecord(
                owner_of=lambda p: ProjectID(p.id),
                operation=OP_SCOPED,
                created_at=LATE,
                triggered_by=UserID(seeding.made(trigger).id),
                scopes=((ProjectEntityType(), scope_id), (UserEntityType(), member_id)),
            ),
            about,
        )
        role = {"superadmin": UserRole.SUPERADMIN, "monitor": UserRole.MONITOR}.get(
            self.reader, UserRole.USER
        )
        caller = await seeding.within(SomeoneOf(domain, role=role))
        match self.reader:
            case "scope":
                await grant_reading(
                    seeding,
                    scope,
                    caller,
                    entity_type=ProjectEntityType(),
                    scope_of=lambda p: ProjectID(p.id),
                )
            case "about":
                await grant_reading(
                    seeding,
                    about,
                    caller,
                    entity_type=ProjectEntityType(),
                    scope_of=lambda p: ProjectID(p.id),
                )
            case "trigger":
                await grant_reading(
                    seeding,
                    trigger,
                    caller,
                    entity_type=UserEntityType(),
                    scope_of=lambda u: UserID(u.id),
                )
        project_scope = ExpectedScope("project", scope_id)
        user_scope = ExpectedScope("user", member_id)
        visible = {
            "all": (project_scope, user_scope),
            "project": (project_scope,),
            "user": (user_scope,),
        }[self.narrow]
        return ScopesToSearch(
            seeding.made(caller), seeding.made(record).id, visible, narrow_id=member_id
        )


@dataclass(frozen=True)
class ARecordWithoutScopes(Given[Any, ScopesToSearch]):
    """A record about one project that recorded no scope, and a caller granted READ on
    that project."""

    @override
    def describe(self) -> str:
        return (
            "범위를 남기지 않은 한 프로젝트의 기록과, 그 프로젝트에 읽기 권한을 받은 사용자 한 명"
        )

    @override
    async def lay(self, seeding: TestSeedingSession) -> ScopesToSearch:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        policy = await seeding.once(TestSeedProjectPolicy())
        project = await seeding.creating_from_two(TestSeedProject(name_hint="team"), domain, policy)
        record = await seeding.adding(
            TestSeedAuditRecord(
                owner_of=lambda p: ProjectID(p.id), operation=OP_OK, created_at=LATE
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
        return ScopesToSearch(seeding.made(caller), seeding.made(record).id, ())


@dataclass(frozen=True)
class NoRecordToSearch(Given[Any, ScopesToSearch]):
    """A superadmin, and a record id nothing answers to."""

    @override
    def describe(self) -> str:
        return "슈퍼관리자 한 명"

    @override
    async def lay(self, seeding: TestSeedingSession) -> ScopesToSearch:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(SomeoneOf(domain, role=UserRole.SUPERADMIN))
        return ScopesToSearch(seeding.made(caller), uuid4(), ())


@dataclass(frozen=True)
class TheScopesAnswered(Then[ScopesToSearch, SearchAuditLogScopesPayload]):
    """The scopes expected come back, in order and whole, and only those."""

    @override
    def says(self) -> str:
        return "기록의 범위가 순서대로, 그리고 그것만 반환된다"

    @override
    def look(
        self, laid: ScopesToSearch, answered: Answered[SearchAuditLogScopesPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Same("answer", repr(answered.raised), "a page of scopes")]
        verdicts: list[Verdict] = [
            Same("item_count", len(payload.items), len(laid.visible)),
            Same("total_count", payload.total_count, len(laid.visible)),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]
        for index, (node, expected) in enumerate(zip(payload.items, laid.visible, strict=False)):
            at = f"[{index}]."
            verdicts.extend([
                Skipped(f"{at}id", "데이터베이스가 만든다"),
                Skipped(f"{at}field_id", "데이터베이스가 만든다"),
                Held(
                    f"{at}audit_log_id", node.audit_log_id, SameAs[UUID](laid.record, "검색한 기록")
                ),
                Same(f"{at}scope_type", node.scope_type, expected.scope_type),
                Held(
                    f"{at}scope_id",
                    node.scope_id,
                    SameAs[UUID](expected.scope_id, "기록이 남긴 범위"),
                ),
            ])
        return verdicts
