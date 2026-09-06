"""The own check's query against the one it replaced, on seeded data.

What this pins down:

- Both queries answer the same bits for every entity, on three data shapes: deep
  own chains (session <- project <- domain), shares clipped by a cap, and a user
  holding many roles on many kinds (the noise the ``held`` CTE is meant to cut).
- A benchmark over the same shapes at a larger size, run only with
  ``BAI_BENCHMARK=1`` and ``-s``: warm-up, then interleaved repetitions of both
  queries, reported as min / median / p95. Nothing is asserted on time — the
  container database varies — so the numbers are read, not gated.
"""

from __future__ import annotations

import os
import statistics
import time
import uuid
from collections import defaultdict
from collections.abc import AsyncGenerator, Awaitable, Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import PROJECT_ENTITY_TYPE
from ai.backend.common.data.entity.session import SESSION_ENTITY_TYPE, SessionID
from ai.backend.common.data.entity.types import EntityID, EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import USER_SCOPE_TYPE, UserID
from ai.backend.common.data.entity.vfolder import VFOLDER_ENTITY_TYPE, VFolderUUID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.virtual_entity import OwnCheckKey
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.permission.permission_field import PermissionFieldRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.entity_membership_field import (
    EntityMembershipFieldRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.permission.provider import PermissionOpsProvider
from ai.backend.manager.repositories.ops.v2.permission.read import PermissionReadOps, _GroupKey
from ai.backend.testutils.db import with_tables

_DOMAIN = EntityType("domain")


@dataclass
class _Seed:
    """What a shape planted: the user and the entities to ask about."""

    user_id: UserID
    entity_type: EntityType
    entity_ids: list[EntityIdentifier] = field(default_factory=list)


type _Plant = Callable[[AsyncSession], Awaitable[_Seed]]
type _Run = Callable[[], Awaitable[Mapping[EntityID, Permission]]]


@pytest.fixture
async def database(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(
        database_connection,
        [
            DomainRow,
            UserResourcePolicyRow,
            KeyPairResourcePolicyRow,
            RoleRow,
            UserRoleRow,
            UserRow,
            KeyPairRow,
            PermissionRow,
            PermissionFieldRow,
            VirtualEntityRow,
            ScopeBindingRow,
            EntityLabelRow,
            EntityMembershipRow,
            EntityMembershipCapRow,
            EntityMembershipFieldRow,
        ],
    ):
        yield database_connection


# =============================================================================
# Seeding
# =============================================================================


async def _node(sess: AsyncSession, entity_type: EntityType, entity_id: uuid.UUID) -> uuid.UUID:
    """A virtual entity that owns and governs itself, as provisioning writes."""
    node = VirtualEntityRow(entity_type=entity_type, entity_id=entity_id)
    sess.add(node)
    await sess.flush()
    sess.add(EntityMembershipRow(virtual_entity_id=node.id, member_entity_id=node.id, capped=False))
    sess.add(
        ScopeBindingRow(virtual_entity_id=node.id, scope_entity_id=node.id, permission_cap=None)
    )
    return node.id


async def _own(sess: AsyncSession, owner_node: uuid.UUID, entity_node: uuid.UUID) -> None:
    sess.add(
        EntityMembershipRow(
            virtual_entity_id=owner_node, member_entity_id=entity_node, capped=False
        )
    )


async def _govern(
    sess: AsyncSession, scope_node: uuid.UUID, entity_node: uuid.UUID, cap: Permission | None = None
) -> None:
    sess.add(
        ScopeBindingRow(
            virtual_entity_id=entity_node, scope_entity_id=scope_node, permission_cap=cap
        )
    )


async def _share(
    sess: AsyncSession, scope_node: uuid.UUID, entity_node: uuid.UUID, cap: Permission
) -> None:
    edge = EntityMembershipRow(
        virtual_entity_id=scope_node, member_entity_id=entity_node, capped=True
    )
    sess.add(edge)
    await sess.flush()
    for bit in Permission:
        if bit and cap & bit:
            sess.add(EntityMembershipCapRow(membership_id=edge.id, permission=bit, all_fields=True))


def _permission_rows(
    role_id: uuid.UUID,
    scope_type: EntityType,
    scope_id: uuid.UUID,
    entity_type: EntityType,
    mask: Permission,
) -> list[PermissionRow]:
    return [
        PermissionRow(
            role_id=role_id,
            scope_type=scope_type,
            scope_id=str(scope_id),
            entity_type=entity_type,
            permission=bit,
        )
        for bit in Permission
        if bit and mask & bit
    ]


async def _user_in_domain(sess: AsyncSession) -> tuple[UserID, DomainID, uuid.UUID, uuid.UUID]:
    """A user in a fresh domain; answers (user, domain, user node, domain node)."""
    domain_id = DomainID(uuid.uuid4())
    domain_name = f"domain-{domain_id.hex[:8]}"
    sess.add(DomainRow(id=domain_id, name=domain_name, total_resource_slots=ResourceSlot()))
    policy_name = f"policy-{domain_id.hex[:8]}"
    sess.add(
        UserResourcePolicyRow(
            name=policy_name,
            max_vfolder_count=0,
            max_quota_scope_size=-1,
            max_session_count_per_model_session=0,
            max_customized_image_count=0,
        )
    )
    user_id = UserID(uuid.uuid4())
    sess.add(
        UserRow(
            uuid=user_id,
            username=f"user-{user_id.hex[:8]}",
            email=f"{user_id.hex[:8]}@test.com",
            resource_policy=policy_name,
            status=UserStatus.ACTIVE,
            need_password_change=False,
            sudo_session_enabled=False,
            domain_name=domain_name,
            domain_id=domain_id,
        )
    )
    await sess.flush()
    domain_node = await _node(sess, _DOMAIN, domain_id)
    user_node = await _node(sess, USER_SCOPE_TYPE, user_id)
    await _govern(sess, domain_node, user_node)
    return user_id, domain_id, user_node, domain_node


async def _role(sess: AsyncSession, user_id: UserID, rows: Sequence[PermissionRow]) -> None:
    role = RoleRow(name=f"role-{uuid.uuid4().hex[:8]}", status=RoleStatus.ACTIVE)
    sess.add(role)
    await sess.flush()
    sess.add(UserRoleRow(user_id=user_id, role_id=role.id))
    for row in rows:
        row.role_id = role.id
        sess.add(row)


async def seed_deep_own(sess: AsyncSession, count: int) -> _Seed:
    """Sessions owned by a project and the user, the project governed by the
    domain; the domain role reads, the project role updates."""
    user_id, domain_id, user_node, domain_node = await _user_in_domain(sess)
    seed = _Seed(user_id=user_id, entity_type=SESSION_ENTITY_TYPE)
    project_id = uuid.uuid4()
    project_node = await _node(sess, PROJECT_ENTITY_TYPE, project_id)
    await _govern(sess, domain_node, project_node)
    await _role(
        sess,
        user_id,
        _permission_rows(uuid.uuid4(), _DOMAIN, domain_id, SESSION_ENTITY_TYPE, Permission.READ),
    )
    await _role(
        sess,
        user_id,
        _permission_rows(
            uuid.uuid4(), PROJECT_ENTITY_TYPE, project_id, SESSION_ENTITY_TYPE, Permission.UPDATE
        ),
    )
    for _ in range(count):
        session_id = SessionID(uuid.uuid4())
        node = await _node(sess, SESSION_ENTITY_TYPE, session_id)
        await _own(sess, project_node, node)
        await _own(sess, user_node, node)
        await _govern(sess, project_node, node)
        await _govern(sess, user_node, node)
        seed.entity_ids.append(session_id)
    return seed


async def seed_shares(sess: AsyncSession, count: int) -> _Seed:
    """Vfolders shared to the user under READ while the user's own scope holds
    READ|UPDATE on vfolders, so the cap clips every answer to READ."""
    user_id, _, user_node, _ = await _user_in_domain(sess)
    seed = _Seed(user_id=user_id, entity_type=VFOLDER_ENTITY_TYPE)
    await _role(
        sess,
        user_id,
        _permission_rows(
            uuid.uuid4(),
            USER_SCOPE_TYPE,
            user_id,
            VFOLDER_ENTITY_TYPE,
            Permission.READ | Permission.UPDATE,
        ),
    )
    for _ in range(count):
        vfolder_id = VFolderUUID(uuid.uuid4())
        node = await _node(sess, VFOLDER_ENTITY_TYPE, vfolder_id)
        await _share(sess, user_node, node, Permission.READ)
        seed.entity_ids.append(vfolder_id)
    return seed


async def seed_many_roles(sess: AsyncSession, count: int, roles: int) -> _Seed:
    """The deep-own shape plus many roles on unrelated kinds, so the user's held
    permissions are wide and the walk must not fan out through them."""
    seed = await seed_deep_own(sess, count)
    domain_id = (
        await sess.execute(sa.select(UserRow.domain_id).where(UserRow.uuid == seed.user_id))
    ).scalar_one()
    for i in range(roles):
        kind = EntityType(f"kind_{i}")
        await _role(
            sess,
            seed.user_id,
            _permission_rows(uuid.uuid4(), _DOMAIN, domain_id, kind, Permission.full()),
        )
    return seed


# =============================================================================
# The query this one replaced
# =============================================================================


async def _previous_query(
    sess: AsyncSession,
    user_id: UserID,
    entity_type: EntityType,
    entity_ids: Sequence[EntityIdentifier],
) -> Mapping[EntityID, Permission]:
    """The own check as it stood before the ``held`` CTE and the SQL-side OR: one row
    per path and bit, clipped and combined in Python."""
    query = _previous_statement(user_id, entity_type, entity_ids)
    full_cap = Permission.full()
    granted: defaultdict[EntityID, Permission] = defaultdict(lambda: Permission.NONE)
    for row in await sess.execute(query):
        scope_cap = row.scope_cap if row.scope_cap is not None else full_cap
        granted[row.entity_id] |= row.permission & scope_cap
    return granted


def _previous_statement(
    user_id: UserID, entity_type: EntityType, entity_ids: Sequence[EntityIdentifier]
) -> sa.Select[Any]:
    em = EntityMembershipRow.__table__
    emc = EntityMembershipCapRow.__table__
    sb = ScopeBindingRow.__table__
    member = VirtualEntityRow.__table__.alias("member_virtual_entity")
    scope = VirtualEntityRow.__table__.alias("scope_virtual_entity")
    perm = PermissionRow.__table__
    roles = RoleRow.__table__
    user_roles = UserRoleRow.__table__
    return (
        sa.select(member.c.entity_id, perm.c.permission, sb.c.permission_cap.label("scope_cap"))
        .select_from(
            em.join(member, member.c.id == em.c.member_entity_id)
            .join(sb, sb.c.virtual_entity_id == em.c.virtual_entity_id)
            .join(scope, scope.c.id == sb.c.scope_entity_id)
            .join(
                perm,
                sa.and_(
                    perm.c.scope_type == scope.c.entity_type,
                    perm.c.scope_id == sa.cast(scope.c.entity_id, sa.String),
                    perm.c.entity_type == entity_type,
                    perm.c.all_fields.is_(True),
                ),
            )
            .join(roles, roles.c.id == perm.c.role_id)
            .join(user_roles, user_roles.c.role_id == roles.c.id)
            .outerjoin(
                emc,
                sa.and_(
                    emc.c.membership_id == em.c.id,
                    emc.c.permission == perm.c.permission,
                    emc.c.all_fields.is_(True),
                ),
            )
        )
        .where(
            member.c.entity_type == entity_type,
            member.c.entity_id.in_(entity_ids),
            user_roles.c.user_id == user_id,
            roles.c.status == RoleStatus.ACTIVE,
            sa.or_(
                em.c.capped.is_(False),
                sa.and_(
                    emc.c.id.is_not(None),
                    member.c.entity_type == entity_type,
                    sb.c.scope_entity_id == sb.c.virtual_entity_id,
                ),
            ),
        )
    )


async def _explain(sess: AsyncSession, statement: sa.Select[Any]) -> str:
    """The plan PostgreSQL ran, as text; binds rendered inline for EXPLAIN."""
    compiled = statement.compile(dialect=sess.bind.dialect, compile_kwargs={"literal_binds": True})
    rows = await sess.execute(sa.text(f"EXPLAIN (ANALYZE, BUFFERS) {compiled}"))
    return "\n".join(f"    {row[0]}" for row in rows)


# =============================================================================
# Equivalence, then the benchmark
# =============================================================================


_SHAPES = [
    pytest.param("deep-own", Permission.READ | Permission.UPDATE, id="deep-own"),
    pytest.param("shares", Permission.READ, id="shares"),
    pytest.param("many-roles", Permission.READ | Permission.UPDATE, id="many-roles"),
]


def _plant(shape: str, entities: int, roles: int) -> _Plant:
    match shape:
        case "deep-own":
            return lambda sess: seed_deep_own(sess, entities)
        case "shares":
            return lambda sess: seed_shares(sess, entities)
        case "many-roles":
            return lambda sess: seed_many_roles(sess, entities, roles)
        case _:
            raise ValueError(shape)


def _runs(database: ExtendedAsyncSAEngine, seed: _Seed) -> tuple[_Run, _Run]:
    """(previous, current) over every entity the seed planted."""
    keys = [OwnCheckKey(user_id=seed.user_id, entity=e) for e in seed.entity_ids]
    provider = PermissionOpsProvider(database)

    async def current() -> Mapping[EntityID, Permission]:
        async with provider.read_ops() as r:
            answered = await r.owned_permissions(keys)
        return {key.entity: bits for key, bits in answered.items()}

    async def previous() -> Mapping[EntityID, Permission]:
        async with database.begin_readonly_session() as sess:
            return dict(
                await _previous_query(sess, seed.user_id, seed.entity_type, seed.entity_ids)
            )

    return previous, current


@pytest.mark.parametrize(("shape", "expected"), _SHAPES)
async def test_the_query_answers_what_the_previous_one_did(
    database: ExtendedAsyncSAEngine, shape: str, expected: Permission
) -> None:
    async with database.begin_session() as sess:
        seed = await _plant(shape, entities=100, roles=20)(sess)
    previous, current = _runs(database, seed)

    answered = await current()
    assert answered == await previous()
    assert set(answered.values()) == {expected}
    assert len(answered) == len(seed.entity_ids)


@pytest.mark.skipif(not os.environ.get("BAI_BENCHMARK"), reason="set BAI_BENCHMARK=1 to run")
@pytest.mark.parametrize(("shape", "expected"), _SHAPES)
async def test_benchmark_against_the_previous_query(
    database: ExtendedAsyncSAEngine, shape: str, expected: Permission
) -> None:
    entities, roles, warmup, repeat = 1000, 100, 3, 30
    async with database.begin_session() as sess:
        seed = await _plant(shape, entities=entities, roles=roles)(sess)
    previous, current = _runs(database, seed)

    for _ in range(warmup):
        await previous()
        await current()
    samples: dict[str, list[float]] = {"previous": [], "current": []}
    for _ in range(repeat):
        for name, run in (("previous", previous), ("current", current)):
            started = time.perf_counter()
            await run()
            samples[name].append((time.perf_counter() - started) * 1000)

    def report(name: str) -> str:
        values = sorted(samples[name])
        p95 = values[min(len(values) - 1, int(len(values) * 0.95))]
        return f"{name}: min {values[0]:.1f}ms  median {statistics.median(values):.1f}ms  p95 {p95:.1f}ms"

    print(f"\n[{shape}] entities={entities} roles={roles} repeat={repeat}")
    print("  " + report("previous"))
    print("  " + report("current"))


# =============================================================================
# The benchmark at scale: COPY-seeded, run only with BAI_BENCHMARK_SCALE=1
# =============================================================================


@dataclass(frozen=True)
class _Scale:
    domains: int = 10
    projects: int = 1_000
    users: int = 10_000
    sessions: int = 1_000_000
    vfolders: int = 1_000_000
    shared_vfolders: int = 200_000
    roles: int = 10_000
    permissions_per_role: int = 10
    roles_per_user: int = 10


@dataclass
class _ScaleSeed:
    user_id: UserID
    owned_sessions: list[EntityIdentifier]
    other_sessions: list[EntityIdentifier]
    shared_vfolders: list[EntityIdentifier]
    other_vfolders: list[EntityIdentifier]


async def _copy(
    conn: Any, table: str, columns: Sequence[str], records: Iterable[tuple[Any, ...]]
) -> None:
    driver = (await conn.get_raw_connection()).driver_connection
    await driver.copy_records_to_table(table, records=records, columns=list(columns))


async def seed_at_scale(database: ExtendedAsyncSAEngine, scale: _Scale) -> _ScaleSeed:
    """Domains govern projects and users; sessions are created in a project and a
    user, vfolders in a user; users are shared into ten projects and a slice of
    vfolders is shared to users; every user holds roles with permissions spread over
    domains, projects and many kinds. Answers the ids the benchmark asks about."""
    domain_ids = [uuid.uuid4() for _ in range(scale.domains)]
    project_ids = [uuid.uuid4() for _ in range(scale.projects)]
    user_ids = [uuid.uuid4() for _ in range(scale.users)]
    session_ids = [uuid.uuid4() for _ in range(scale.sessions)]
    vfolder_ids = [uuid.uuid4() for _ in range(scale.vfolders)]
    node = {}  # entity id -> virtual entity id

    def nodes() -> Iterable[tuple[uuid.UUID, str, uuid.UUID]]:
        for kind, ids in (
            (str(_DOMAIN), domain_ids),
            (str(PROJECT_ENTITY_TYPE), project_ids),
            (str(USER_SCOPE_TYPE), user_ids),
            (str(SESSION_ENTITY_TYPE), session_ids),
            (str(VFOLDER_ENTITY_TYPE), vfolder_ids),
        ):
            for entity_id in ids:
                node_id = uuid.uuid4()
                node[entity_id] = node_id
                yield (node_id, kind, entity_id)

    def self_own() -> Iterable[tuple[uuid.UUID, uuid.UUID, bool]]:
        return ((n, n, False) for n in node.values())

    def self_govern() -> Iterable[tuple[uuid.UUID, uuid.UUID, None]]:
        return ((n, n, None) for n in node.values())

    def project_of(i: int) -> uuid.UUID:
        return project_ids[i % scale.projects]

    def user_of(i: int) -> uuid.UUID:
        return user_ids[(i // scale.projects) % scale.users]

    def own() -> Iterable[tuple[uuid.UUID, uuid.UUID, bool]]:
        for i, sid in enumerate(session_ids):
            yield (node[project_of(i)], node[sid], False)
            yield (node[user_of(i)], node[sid], False)
        for i, vid in enumerate(vfolder_ids):
            yield (node[user_ids[i % scale.users]], node[vid], False)

    def govern() -> Iterable[tuple[uuid.UUID, uuid.UUID, None]]:
        for i, pid in enumerate(project_ids):
            yield (node[pid], node[domain_ids[i % scale.domains]], None)
        for i, uid in enumerate(user_ids):
            yield (node[uid], node[domain_ids[i % scale.domains]], None)
        for i, sid in enumerate(session_ids):
            yield (node[sid], node[project_of(i)], None)
            yield (node[sid], node[user_of(i)], None)
        for i, vid in enumerate(vfolder_ids):
            yield (node[vid], node[user_ids[i % scale.users]], None)

    share_ids: list[uuid.UUID] = []

    def shares() -> Iterable[tuple[uuid.UUID, uuid.UUID, uuid.UUID, bool]]:
        # every user shared into ten projects (the roster), READ on every field
        for i, uid in enumerate(user_ids):
            for k in range(10):
                sid = uuid.uuid4()
                share_ids.append(sid)
                yield (sid, node[project_ids[(i + k) % scale.projects]], node[uid], True)
        # a slice of vfolders shared to a user other than the owner
        for i in range(scale.shared_vfolders):
            sid = uuid.uuid4()
            share_ids.append(sid)
            # to the user after the owner, so the share never doubles the own edge
            yield (sid, node[user_ids[(i + 1) % scale.users]], node[vfolder_ids[i]], True)

    def share_caps() -> Iterable[tuple[uuid.UUID, int, bool]]:
        return ((sid, int(Permission.READ), True) for sid in share_ids)

    role_ids = [uuid.uuid4() for _ in range(scale.roles)]
    measured = user_ids[0]
    domain_role, vfolder_role = uuid.uuid4(), uuid.uuid4()
    project_roles = [uuid.uuid4() for _ in range(10)]

    def roles() -> Iterable[tuple[uuid.UUID, str, str, str, bool]]:
        for i, rid in enumerate(role_ids):
            yield (rid, f"role-{i}", "system", "active", False)
        yield (domain_role, "measured-domain", "system", "active", False)
        yield (vfolder_role, "measured-vfolder", "system", "active", False)
        for i, rid in enumerate(project_roles):
            yield (rid, f"measured-project-{i}", "system", "active", False)

    def permissions() -> Iterable[tuple[uuid.UUID, str, str, str, int, bool]]:
        kinds = [str(SESSION_ENTITY_TYPE), str(VFOLDER_ENTITY_TYPE)] + [
            f"kind_{k}" for k in range(8)
        ]
        for i, rid in enumerate(role_ids):
            for k in range(scale.permissions_per_role):
                if i % 2:
                    scope_type, scope_id = (
                        str(PROJECT_ENTITY_TYPE),
                        project_ids[(i + k) % scale.projects],
                    )
                else:
                    scope_type, scope_id = str(_DOMAIN), domain_ids[(i + k) % scale.domains]
                bit = int(Permission.READ) if k % 2 else int(Permission.UPDATE)
                yield (rid, scope_type, str(scope_id), kinds[k % len(kinds)], bit, True)
        yield (
            domain_role,
            str(_DOMAIN),
            str(domain_ids[0]),
            str(SESSION_ENTITY_TYPE),
            int(Permission.READ),
            True,
        )
        for bit in (Permission.READ, Permission.UPDATE):
            yield (
                vfolder_role,
                str(USER_SCOPE_TYPE),
                str(measured),
                str(VFOLDER_ENTITY_TYPE),
                int(bit),
                True,
            )
        for i, rid in enumerate(project_roles):
            yield (
                rid,
                str(PROJECT_ENTITY_TYPE),
                str(project_ids[i]),
                str(SESSION_ENTITY_TYPE),
                int(Permission.UPDATE),
                True,
            )

    def user_roles() -> Iterable[tuple[uuid.UUID, uuid.UUID]]:
        for i, uid in enumerate(user_ids):
            for k in range(scale.roles_per_user):
                yield (uid, role_ids[(i * scale.roles_per_user + k) % scale.roles])
        yield (measured, domain_role)
        yield (measured, vfolder_role)
        for rid in project_roles:
            yield (measured, rid)

    async with database.begin_session() as sess:
        for i, did in enumerate(domain_ids):
            sess.add(DomainRow(id=did, name=f"domain-{i}", total_resource_slots=ResourceSlot()))
        sess.add(
            UserResourcePolicyRow(
                name="scale-policy",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=0,
                max_customized_image_count=0,
            )
        )

    async with database.begin() as conn:
        await _copy(
            conn,
            "users",
            [
                "uuid",
                "username",
                "email",
                "need_password_change",
                "status",
                "domain_name",
                "domain_id",
                "role",
                "totp_activated",
                "resource_policy",
                "sudo_session_enabled",
            ],
            (
                (
                    uid,
                    f"user-{i}",
                    f"user-{i}@scale.test",
                    False,
                    "active",
                    f"domain-{i % scale.domains}",
                    domain_ids[i % scale.domains],
                    "user",
                    False,
                    "scale-policy",
                    False,
                )
                for i, uid in enumerate(user_ids)
            ),
        )
        await _copy(conn, "virtual_entities", ["id", "entity_type", "entity_id"], nodes())
        await _copy(
            conn,
            "entity_memberships",
            ["virtual_entity_id", "member_entity_id", "capped"],
            self_own(),
        )
        await _copy(
            conn,
            "scope_bindings",
            ["virtual_entity_id", "scope_entity_id", "permission_cap"],
            self_govern(),
        )
        await _copy(
            conn, "entity_memberships", ["virtual_entity_id", "member_entity_id", "capped"], own()
        )
        await _copy(
            conn,
            "scope_bindings",
            ["virtual_entity_id", "scope_entity_id", "permission_cap"],
            govern(),
        )
        await _copy(
            conn,
            "entity_memberships",
            ["id", "virtual_entity_id", "member_entity_id", "capped"],
            shares(),
        )
        await _copy(
            conn,
            "entity_membership_caps",
            ["membership_id", "permission", "all_fields"],
            share_caps(),
        )
        await _copy(conn, "roles", ["id", "name", "source", "status", "auto_assign"], roles())
        await _copy(
            conn,
            "permissions",
            ["role_id", "scope_type", "scope_id", "entity_type", "permission", "all_fields"],
            permissions(),
        )
        await _copy(conn, "user_roles", ["user_id", "role_id"], user_roles())
        await conn.execute(sa.text("ANALYZE"))

    owned: list[EntityIdentifier] = [
        SessionID(session_ids[i]) for i in range(scale.projects)
    ]  # user_of(i) == measured
    others: list[EntityIdentifier] = [
        SessionID(session_ids[i])
        for i in range(scale.sessions // 2, scale.sessions // 2 + scale.projects)
    ]
    shared: list[EntityIdentifier] = [  # owned by the last user, shared to user 0
        VFolderUUID(vfolder_ids[scale.users - 1 + scale.users * k])
        for k in range(scale.shared_vfolders // scale.users)
    ]
    unshared: list[EntityIdentifier] = [
        VFolderUUID(vfolder_ids[i])
        for i in range(scale.shared_vfolders, scale.shared_vfolders + 480)
    ]
    return _ScaleSeed(UserID(measured), owned, others, shared, unshared)


@pytest.mark.skipif(
    not os.environ.get("BAI_BENCHMARK_SCALE"), reason="set BAI_BENCHMARK_SCALE=1 to run"
)
async def test_benchmark_at_scale(database: ExtendedAsyncSAEngine) -> None:
    scale = _Scale()
    started = time.perf_counter()
    seed = await seed_at_scale(database, scale)
    print(f"\n[scale] seeded in {time.perf_counter() - started:.0f}s: {scale}")

    cases = {
        "sessions (1000 owned + 1000 others)": (
            SESSION_ENTITY_TYPE,
            seed.owned_sessions + seed.other_sessions,
        ),
        f"vfolders ({len(seed.shared_vfolders)} shared + {len(seed.other_vfolders)} unshared)": (
            VFOLDER_ENTITY_TYPE,
            seed.shared_vfolders + seed.other_vfolders,
        ),
    }
    provider = PermissionOpsProvider(database)
    for name, (entity_type, entity_ids) in cases.items():
        keys = [OwnCheckKey(user_id=seed.user_id, entity=e) for e in entity_ids]

        async def current() -> Mapping[EntityID, Permission]:
            async with provider.read_ops() as r:
                answered = await r.owned_permissions(keys)
            # The previous query left unreached entities out; the current one maps
            # them to NONE. Compare what is reached.
            return {key.entity: bits for key, bits in answered.items() if bits}

        async def previous() -> Mapping[EntityID, Permission]:
            async with database.begin_readonly_session() as sess:
                return dict(await _previous_query(sess, seed.user_id, entity_type, entity_ids))

        reached = await current()
        assert reached == await previous()
        print(f"[scale] {name}: reached {len(reached)} of {len(entity_ids)}")
        samples: dict[str, list[float]] = {"previous": [], "current": []}
        for _ in range(2):
            await previous()
            await current()
        for _ in range(5):
            for run_name, run in (("previous", previous), ("current", current)):
                begun = time.perf_counter()
                await run()
                samples[run_name].append((time.perf_counter() - begun) * 1000)
        print(f"[scale] {name}")
        for run_name in ("previous", "current"):
            values = sorted(samples[run_name])
            p95 = values[min(len(values) - 1, int(len(values) * 0.95))]
            print(
                f"  {run_name}: min {values[0]:.1f}ms  median {statistics.median(values):.1f}ms  p95 {p95:.1f}ms"
            )
        group = _GroupKey(
            user_id=seed.user_id, entity_type=entity_type, subject_entity_type=entity_type
        )
        async with database.begin_readonly_session() as sess:
            print("[scale] plan, previous:")
            print(await _explain(sess, _previous_statement(seed.user_id, entity_type, entity_ids)))
            print("[scale] plan, current:")
            print(await _explain(sess, PermissionReadOps(sess)._owned_query(group, entity_ids)))
