"""Scenario data seeded into a start schema before upgrading it.

Each scenario seeds what an operating site may hold, upgrades through ``steps`` and
checks the result. ``requires`` lists the revisions a scenario exercises; it is skipped
for a start that has already applied them. Seeds assume the 26.4 / 25.15 table shapes.
"""

from __future__ import annotations

import datetime
import os
import uuid
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

import asyncpg
from schema_values import RULES, ValueRule, seed_duplicates, seed_rule
from seeding import Seeder

type Seed = Callable[[Seeder], Awaitable[None]]
type Verify = Callable[[asyncpg.Connection], Awaitable[list[str]]]

GHOST_USER = uuid.UUID("00000000-0000-4000-8000-00000000dead")
GHOST_PROJECT = uuid.UUID("00000000-0000-4000-8000-0000000000ef")
SCALE_ROWS = int(os.environ.get("UPGRADE_CHECK_ROWS", "100000"))
SCALE_USERS = int(os.environ.get("UPGRADE_CHECK_USERS", "6000"))


async def _no_seed(_: Seeder) -> None:
    return None


async def _no_problems(_: asyncpg.Connection) -> list[str]:
    return []


@dataclass(frozen=True)
class Scenario:
    name: str
    description: str
    seed: Seed = _no_seed
    verify: Verify = _no_problems
    steps: tuple[str, ...] = ("head",)
    checks_after: Mapping[str, Verify] = field(default_factory=dict)
    expect_error: str | None = None
    requires: tuple[str, ...] = ()


class SkipScenario(Exception):
    """The start schema lacks what the scenario seeds."""


def _require_tables(s: Seeder, *tables: str) -> None:
    missing = [t for t in tables if not s.has_table(t)]
    if missing:
        raise SkipScenario(f"no table {', '.join(missing)} at this start")


async def _default_ids(s: Seeder) -> dict[str, Any]:
    row = await s.conn.fetchrow(
        """
        SELECT d.name AS domain, g.id AS project, u.uuid AS user,
               (SELECT name FROM scaling_groups ORDER BY name LIMIT 1) AS sgroup
        FROM domains d
        JOIN groups g ON g.domain_name = d.name AND g.name = 'default'
        JOIN users u ON u.email = 'user@lablup.com'
        WHERE d.name = 'default'
        """
    )
    return dict(row)


async def _session(s: Seeder, ids: Mapping[str, Any], user: uuid.UUID, **extra: Any) -> Any:
    session = await s.insert(
        "sessions",
        id=uuid.uuid4(),
        name=f"s-{uuid.uuid4().hex[:8]}",
        domain_name=ids["domain"],
        group_id=ids["project"],
        user_uuid=user,
        scaling_group_name=ids["sgroup"],
        status="TERMINATED",
        **extra,
    )
    await s.insert(
        "kernels",
        id=uuid.uuid4(),
        session_id=session["id"],
        domain_name=ids["domain"],
        group_id=ids["project"],
        user_uuid=user,
        scaling_group=ids["sgroup"],
        cluster_role="main",
        cluster_idx=0,
        local_rank=0,
        cluster_hostname="main1",
        status="TERMINATED",
    )
    return session


# --- deployments owned by a deleted user (8f3c1d5a2b47) -------------------------------


async def seed_deleted_deployment_owner(s: Seeder) -> None:
    """Deployments whose owner was deleted: two whose creator is gone too, one whose creator
    remains, with a token each. ``routings.session_owner`` is a RESTRICT FK, so a deleted
    owner has no routes left; a live owner's deployment carries a route session for the
    membership backfill."""
    ids = await _default_ids(s)
    # Before 26.4 an endpoint that is not destroyed must name an image.
    image: dict[str, Any] = {}
    if s.has_column("endpoints", "image"):
        image = {
            "image": (
                await s.insert(
                    "images",
                    name="cr.example.com/test/python:3.13",
                    image="test/python",
                    registry="cr.example.com",
                    architecture="x86_64",
                )
            )["id"]
        }
    for name, creator, owner, stage in (
        ("ghost-ready", GHOST_USER, GHOST_USER, "ready"),
        ("ghost-destroyed", GHOST_USER, GHOST_USER, "destroyed"),
        ("ghost-owner-live-creator", ids["user"], GHOST_USER, "ready"),
        ("live-ready", ids["user"], ids["user"], "ready"),
    ):
        endpoint = await s.insert(
            "endpoints",
            id=uuid.uuid4(),
            name=name,
            created_user=creator,
            session_owner=owner,
            domain=ids["domain"],
            project=ids["project"],
            resource_group=ids["sgroup"],
            lifecycle_stage=stage,
            **image,
        )
        # Before 26.4 the replica groups are backfilled from the endpoints.
        group = None
        if s.has_table("replica_groups"):
            group = await s.insert("replica_groups", id=uuid.uuid4(), deployment_id=endpoint["id"])
        await s.insert(
            "endpoint_tokens",
            id=uuid.uuid4(),
            token=f"token-{name}",
            endpoint=endpoint["id"],
            session_owner=owner,
            domain=ids["domain"],
            project=ids["project"],
        )
        if owner == GHOST_USER:
            continue
        session = await _session(s, ids, owner)
        route: dict[str, Any] = {"replica_group_id": group["id"]} if group else {}
        await s.insert(
            "routings",
            id=uuid.uuid4(),
            endpoint=endpoint["id"],
            session=session["id"],
            session_owner=owner,
            domain=ids["domain"],
            project=ids["project"],
            **route,
        )


async def verify_deleted_deployment_owner(conn: asyncpg.Connection) -> list[str]:
    problems = []
    rows = await conn.fetch(
        """
        SELECT e.name, e.session_owner = u.uuid AS to_creator,
               (SELECT bool_and(t.session_owner = u.uuid) FROM endpoint_tokens t
                WHERE t.endpoint = e.id) AS tokens_to_creator
        FROM endpoints e JOIN users u ON u.email = 'user@lablup.com'
        WHERE e.name LIKE 'ghost-%' OR e.name = 'live-ready'
        """
    )
    left = {r["name"]: r for r in rows}
    if set(left) != {"ghost-owner-live-creator", "live-ready"}:
        problems.append(f"deployments left {sorted(left)}, expected the reassigned and live ones")
    reassigned = left.get("ghost-owner-live-creator")
    if reassigned is not None and not (
        reassigned["to_creator"] and reassigned["tokens_to_creator"]
    ):
        problems.append("ghost-owner-live-creator and its token were not passed to the creator")
    tokens = await conn.fetchval(
        "SELECT count(*) FROM endpoint_tokens WHERE token IN ('token-ghost-ready', 'token-ghost-destroyed')"
    )
    if tokens:
        problems.append(f"{tokens} token(s) of removed deployments left")
    orphaned = await conn.fetchval(
        "SELECT count(*) FROM session_groups sg"
        " WHERE NOT EXISTS (SELECT 1 FROM users u WHERE u.uuid = sg.owner_user_id)"
    )
    if orphaned:
        problems.append(f"{orphaned} session group(s) owned by a deleted user")
    members = await conn.fetchval(
        "SELECT count(*) FROM sessions s JOIN routings r ON r.session = s.id"
        " WHERE s.session_group_id IS NOT NULL"
    )
    if members != 1:
        problems.append(f"expected 1 route session in a group, got {members}")
    return problems + await verify_owner_fk_validated(conn)


async def verify_owner_fk_validated(conn: asyncpg.Connection) -> list[str]:
    validated = await conn.fetchval(
        "SELECT convalidated FROM pg_constraint WHERE conname = 'fk_session_groups_owner_user_id_users'"
    )
    return [] if validated else [f"owner FK convalidated={validated}, expected validated"]


# --- fair-share rebuild from kernel_usage_records (bd1bf0524350, c4a91d7e05b2) --------


async def seed_fair_share_usage(s: Seeder) -> None:
    _require_tables(s, "kernel_usage_records", "user_usage_buckets")
    ids = await _default_ids(s)
    today = datetime.datetime.now(datetime.UTC).date()
    days = [today - datetime.timedelta(days=d) for d in (3, 2, 1)]
    for day in days:
        start = datetime.datetime.combine(day, datetime.time(1), tzinfo=datetime.UTC)
        for _ in range(2):
            await s.insert(
                "kernel_usage_records",
                kernel_id=uuid.uuid4(),
                session_id=uuid.uuid4(),
                user_uuid=ids["user"],
                project_id=ids["project"],
                domain_name=ids["domain"],
                resource_group=ids["sgroup"],
                period_start=start,
                period_end=start + datetime.timedelta(minutes=5),
                resource_usage={"cpu": "10", "mem": "1000"},
            )
        keys = {
            "user_usage_buckets": {"user_uuid": ids["user"], "project_id": ids["project"]},
            "project_usage_buckets": {"project_id": ids["project"]},
            "domain_usage_buckets": {},
        }
        for table, key in keys.items():
            bucket = await s.insert(
                table,
                domain_name=ids["domain"],
                resource_group=ids["sgroup"],
                period_start=day,
                period_end=day + datetime.timedelta(days=1),
                decay_unit_days=1,
                resource_usage={"cpu": "999999"},
                capacity_snapshot={},
                **key,
            )
            # From 26.4.9 the entry holds the product as resource_usage.
            amount = (
                {"amount": 999999, "duration_seconds": 300}
                if s.has_column("usage_bucket_entries", "amount")
                else {"resource_usage": 999999}
            )
            await s.insert(
                "usage_bucket_entries",
                bucket_id=bucket["id"],
                bucket_type=table.removesuffix("_usage_buckets"),
                slot_name="cpu",
                capacity=0,
                **amount,
            )


async def verify_fair_share_usage(conn: asyncpg.Connection) -> list[str]:
    rows = await conn.fetch(
        """
        SELECT b.period_start, e.resource_usage
        FROM user_usage_buckets b JOIN usage_bucket_entries e
          ON e.bucket_id = b.id AND e.bucket_type = 'user' AND e.slot_name = 'cpu'
        ORDER BY b.period_start
        """
    )
    got = [int(r["resource_usage"]) for r in rows]
    # The oldest day is outside the rebuildable range and keeps its value.
    return (
        []
        if got == [999999, 20, 20]
        else [f"user cpu usage per day {got}, expected [999999, 20, 20]"]
    )


# --- permission rows naming another scope than their role's (c092d242a027) ------------


async def _second_domain_and_project(s: Seeder) -> tuple[Any, Any]:
    ids = await _default_ids(s)
    # Before 26.4 a domain has no id column; a migration gives it one.
    extra = {"id": uuid.uuid4()} if s.has_column("domains", "id") else {}
    domain = await s.insert("domains", name="second", is_active=True, **extra)
    policy = await s.conn.fetchval(
        "SELECT resource_policy FROM groups WHERE id = $1", ids["project"]
    )
    project = await s.insert(
        "groups",
        id=uuid.uuid4(),
        name="second-project",
        domain_name=ids["domain"],
        resource_policy=policy,
        type="general",
        is_active=True,
    )
    return domain, project


async def seed_system_role_in_two_domains(s: Seeder) -> None:
    """From 25.15 the migrations themselves spread the superadmin and monitor rows over
    every domain; from 26.4 the rows they would have spread are added by hand."""
    domain, _ = await _second_domain_and_project(s)
    if not s.has_column("permissions", "scope_type"):
        return
    rows = await s.conn.fetch(
        """
        SELECT p.role_id, p.entity_type, p.operation, p.permission FROM permissions p
        JOIN roles r ON r.id = p.role_id
        WHERE r.name IN ('role_superadmin', 'role_monitor') AND p.scope_type = 'domain'
        """
    )
    for r in rows:
        await s.insert(
            "permissions",
            role_id=r["role_id"],
            scope_type="domain",
            scope_id=str(domain["id"]),
            entity_type=r["entity_type"],
            operation=r["operation"],
            permission=r["permission"],
        )


async def _custom_role(s: Seeder, grants: list[tuple[str, str, str, str]]) -> Any:
    """A custom role held by user@lablup.com; ``grants`` are (scope type, scope id,
    entity type, operation)."""
    role = await s.insert(
        "roles", id=uuid.uuid4(), name="custom-ops", source="custom", status="active"
    )
    ids = await _default_ids(s)
    await s.insert("user_roles", user_id=ids["user"], role_id=role["id"])
    for scope_type, scope_id, entity_type, operation in grants:
        if s.has_column("permissions", "scope_type"):
            await s.insert(
                "permissions",
                role_id=role["id"],
                scope_type=scope_type,
                scope_id=scope_id,
                entity_type=entity_type,
                operation=operation,
                permission=1,
            )
            continue
        # Before 26.4 the scope sits on a permission group.
        group_id = await s.conn.fetchval(
            "SELECT id FROM permission_groups WHERE role_id = $1 AND scope_type = $2"
            " AND scope_id = $3",
            role["id"],
            scope_type,
            scope_id,
        )
        if group_id is None:
            group_id = (
                await s.insert(
                    "permission_groups",
                    role_id=role["id"],
                    scope_type=scope_type,
                    scope_id=scope_id,
                )
            )["id"]
        await s.insert(
            "permissions",
            permission_group_id=group_id,
            entity_type=entity_type,
            operation=operation,
        )
    return role


async def seed_custom_role_on_deleted_project(s: Seeder) -> None:
    project = str((await _default_ids(s))["project"])
    await _custom_role(
        s,
        [
            ("project", project, "session", "read"),
            ("project", project, "vfolder", "read"),
            ("project", str(GHOST_PROJECT), "session", "read"),
        ],
    )


async def seed_custom_role_on_two_projects(s: Seeder) -> None:
    project = str((await _default_ids(s))["project"])
    _, second = await _second_domain_and_project(s)
    await _custom_role(
        s,
        [
            ("project", project, "session", "read"),
            ("project", project, "vfolder", "read"),
            ("project", str(second["id"]), "session", "read"),
        ],
    )


async def mismatch_present(conn: asyncpg.Connection) -> list[str]:
    count = await conn.fetchval(
        """
        SELECT count(*) FROM permissions p JOIN roles r ON r.id = p.role_id
        WHERE p.scope_type IS DISTINCT FROM r.scope_type
           OR p.scope_id IS DISTINCT FROM CAST(r.scope_id AS text)
        """
    )
    return [] if count else ["no mismatched permission rows reached c092d242a027; seed is moot"]


async def verify_custom_role_kept(conn: asyncpg.Connection) -> list[str]:
    count = await conn.fetchval(
        "SELECT count(*) FROM permissions p JOIN roles r ON r.id = p.role_id WHERE r.name = 'custom-ops'"
    )
    return [] if count else ["custom-ops lost all its permissions"]


# --- other risks found in the survey --------------------------------------------------


async def seed_share_of_deleted_owner(s: Seeder) -> None:
    ids = await _default_ids(s)
    folder = await s.insert(
        "vfolders",
        id=uuid.uuid4(),
        host="local:volume1",
        domain_name=ids["domain"],
        quota_scope_id=f"user:{GHOST_USER}",
        name="ghost-folder",
        usage_mode="general",
        ownership_type="user",
        user=GHOST_USER,
        creator="ghost@example.com",
        status="ready",
    )
    await s.insert("vfolder_permissions", vfolder=folder["id"], user=ids["user"], permission="ro")


async def verify_share_of_deleted_owner(conn: asyncpg.Connection) -> list[str]:
    shares = await conn.fetchval(
        """
        SELECT count(*) FROM entity_shares s JOIN vfolders v ON v.id = s.target_entity_id
        WHERE v.name = 'ghost-folder' AND s.status = 'accepted' AND s.sharer_user_id IS NULL
        """
    )
    policies = await conn.fetchval(
        """
        SELECT count(*) FROM vfolder_user_mount_policies p JOIN vfolders v ON v.id = p.vfolder_id
        WHERE v.name = 'ghost-folder'
        """
    )
    problems = []
    if shares != 1:
        problems.append(f"expected 1 accepted share without a sharer, got {shares}")
    if policies != 1:
        problems.append(f"expected 1 mount policy for the recipient, got {policies}")
    return problems


async def seed_same_named_personal_folders(s: Seeder) -> None:
    ids = await _default_ids(s)
    for status in ("delete-pending", "ready"):
        await s.insert(
            "vfolders",
            id=uuid.uuid4(),
            host="local:volume1",
            domain_name=ids["domain"],
            quota_scope_id=f"user:{ids['user']}",
            name="data",
            usage_mode="general",
            ownership_type="user",
            user=ids["user"],
            creator="user@lablup.com",
            status=status,
        )


async def seed_sessions_of_deleted_users(s: Seeder) -> None:
    ids = await _default_ids(s)
    for _ in range(3):
        await _session(s, ids, GHOST_USER)


async def seed_vfolders_without_timestamps(s: Seeder) -> None:
    ids = await _default_ids(s)
    folder = await s.insert(
        "vfolders",
        id=uuid.uuid4(),
        host="local:volume1",
        domain_name=ids["domain"],
        quota_scope_id=f"user:{ids['user']}",
        name="old-folder",
        usage_mode="general",
        ownership_type="user",
        user=ids["user"],
        creator="user@lablup.com",
        status="ready",
    )
    await s.conn.execute(
        "UPDATE vfolders SET created_at = NULL, last_used = NULL WHERE id = $1", folder["id"]
    )


async def seed_scale(s: Seeder) -> None:
    """Grow the tables the survey flags as rewritten in place to ``UPGRADE_CHECK_ROWS``."""
    ids = await _default_ids(s)
    session = await _session(s, ids, ids["user"])
    kernel = await s.conn.fetchval("SELECT id FROM kernels WHERE session_id = $1", session["id"])
    n = SCALE_ROWS
    await s.clone("sessions", session["id"], n - 1, {"id": "uuid_generate_v4()"})
    await s.conn.execute(
        """
        CREATE TEMP TABLE _scale_sessions AS
        SELECT id, row_number() OVER () AS rn FROM sessions;
        CREATE INDEX ON _scale_sessions (rn);
        """
    )
    await s.clone(
        "kernels",
        kernel,
        n - 1,
        {
            "id": "uuid_generate_v4()",
            "session_id": "(SELECT id FROM _scale_sessions WHERE rn = g)",
        },
    )
    if s.has_table("audit_logs"):
        log = await s.insert(
            "audit_logs",
            entity_type="session",
            operation="create",
            entity_id=str(session["id"]),
            triggered_by=str(ids["user"]),
            status="success",
            description="seed",
        )
        await s.clone("audit_logs", log["id"], n - 1, {"id": "uuid_generate_v4()"})
    if not s.has_table("kernel_usage_records"):
        await s.conn.execute("ANALYZE")
        return
    today = datetime.datetime.now(datetime.UTC).date()
    record = await s.insert(
        "kernel_usage_records",
        kernel_id=kernel,
        session_id=session["id"],
        user_uuid=ids["user"],
        project_id=ids["project"],
        domain_name=ids["domain"],
        resource_group=ids["sgroup"],
        period_start=datetime.datetime.combine(today, datetime.time(1), tzinfo=datetime.UTC),
        period_end=datetime.datetime.combine(today, datetime.time(1, 5), tzinfo=datetime.UTC),
        resource_usage={"cpu": "10", "mem": "1000"},
    )
    await s.clone(
        "kernel_usage_records",
        record["id"],
        5 * n - 1,
        {
            "id": "uuid_generate_v4()",
            "period_start": "now() - (g % 30) * interval '1 day'",
            "period_end": "now() - (g % 30) * interval '1 day' + interval '5 minutes'",
        },
    )
    await s.conn.execute("ANALYZE")


async def seed_many_users(s: Seeder) -> None:
    """``UPGRADE_CHECK_USERS`` users shaped like user@lablup.com, with the same project
    membership. From 26.4 each also gets the self role and permissions the runtime makes;
    before 26.4 the migrations make them."""
    ids = await _default_ids(s)
    overrides = {
        "uuid": "uuid_generate_v4()",
        "email": "'bulk-' || g || '@example.com'",
        "username": "'bulk-' || g",
    }
    if s.has_column("users", "main_access_key"):
        overrides["main_access_key"] = "NULL"
    await s.clone("users", ids["user"], SCALE_USERS, overrides, key="uuid")
    await s.conn.execute(
        """
        INSERT INTO association_groups_users (user_id, group_id)
        SELECT u.uuid, a.group_id FROM users u
        JOIN association_groups_users a
          ON a.user_id = (SELECT uuid FROM users WHERE email = 'user@lablup.com')
        WHERE u.email LIKE 'bulk-%'
        """
    )
    if s.has_column("permissions", "scope_type"):
        await s.conn.execute(
            """
            INSERT INTO roles (id, name, source, status)
            SELECT uuid_generate_v4(), 'role_user_' || u.username, 'system', 'active'
            FROM users u WHERE u.email LIKE 'bulk-%';

            INSERT INTO user_roles (user_id, role_id)
            SELECT u.uuid, r.id FROM users u JOIN roles r ON r.name = 'role_user_' || u.username
            WHERE u.email LIKE 'bulk-%';

            INSERT INTO permissions
                (role_id, scope_type, scope_id, entity_type, operation, permission)
            SELECT r.id, p.scope_type, u.uuid::text, p.entity_type, p.operation, p.permission
            FROM users u
            JOIN roles r ON r.name = 'role_user_' || u.username
            JOIN permissions p ON p.role_id = (SELECT id FROM roles WHERE name = 'role_user_user')
            WHERE u.email LIKE 'bulk-%';

            INSERT INTO association_scopes_entities
                (scope_type, scope_id, entity_type, entity_id, relation_type)
            SELECT a.scope_type, a.scope_id, a.entity_type, u.uuid::text, a.relation_type
            FROM users u
            JOIN association_scopes_entities a
              ON a.entity_type = 'user'
             AND a.entity_id = (SELECT uuid::text FROM users WHERE email = 'user@lablup.com')
            WHERE u.email LIKE 'bulk-%';
            """
        )
    await s.conn.execute("ANALYZE")


def _rule_seed(rule: ValueRule) -> Seed:
    async def seed(s: Seeder) -> None:
        await seed_rule(s, rule)

    return seed


SCENARIOS: dict[str, Scenario] = {
    s.name: s
    for s in [
        Scenario("baseline", "install fixtures only"),
        Scenario(
            "deleted_deployment_owner",
            "deployments whose session_owner was deleted, with and without a remaining creator",
            seed_deleted_deployment_owner,
            verify_deleted_deployment_owner,
            requires=("8f3c1d5a2b47",),
        ),
        Scenario(
            "fair_share_usage",
            "three days of kernel_usage_records and inflated usage buckets",
            seed_fair_share_usage,
            verify_fair_share_usage,
            requires=("c4a91d7e05b2",),
        ),
        Scenario(
            "fair_share_and_owner_resumed",
            "the two above, upgraded in the steps an operator took on site",
            seed=lambda s: _chain(s, seed_fair_share_usage, seed_deleted_deployment_owner),
            verify=lambda c: _chain_verify(
                c, verify_fair_share_usage, verify_deleted_deployment_owner
            ),
            steps=("71cb16a7a9c5", "890490020974", "c7d419b0a58e", "head"),
            requires=("8f3c1d5a2b47",),
        ),
        Scenario(
            "system_role_in_two_domains",
            "superadmin and monitor rows spread over a second domain",
            seed_system_role_in_two_domains,
            steps=("c7d419b0a58e", "head"),
            checks_after={"c7d419b0a58e": mismatch_present},
            requires=("c092d242a027",),
        ),
        Scenario(
            "custom_role_on_deleted_project",
            "a custom role whose minority rows name a deleted project",
            seed_custom_role_on_deleted_project,
            verify_custom_role_kept,
            steps=("c7d419b0a58e", "head"),
            checks_after={"c7d419b0a58e": mismatch_present},
            requires=("c092d242a027",),
        ),
        Scenario(
            "custom_role_on_two_projects",
            "a custom role granted on two live projects (left to the operator)",
            seed_custom_role_on_two_projects,
            steps=("c7d419b0a58e", "head"),
            checks_after={"c7d419b0a58e": mismatch_present},
            expect_error="name a scope other than their role's",
            requires=("c092d242a027",),
        ),
        Scenario(
            "share_of_deleted_owner",
            "a folder of a deleted user still shared with a live user",
            seed_share_of_deleted_owner,
            verify_share_of_deleted_owner,
            requires=("e5b8d3f0a129",),
        ),
        Scenario(
            "same_named_personal_folders",
            "a trashed and a live personal folder with the same name",
            seed_same_named_personal_folders,
            expect_error="hold more than one live vfolder of the same name",
            requires=("b4c2e7f19a30",),
        ),
        Scenario(
            "sessions_of_deleted_users",
            "terminated sessions whose user was deleted",
            seed_sessions_of_deleted_users,
        ),
        Scenario(
            "vfolders_without_timestamps",
            "a folder with neither created_at nor last_used",
            seed_vfolders_without_timestamps,
            requires=("5a139f0e951e",),
        ),
        Scenario(
            "many_users",
            "UPGRADE_CHECK_USERS users with a self role and project membership each",
            seed_many_users,
        ),
        *[
            Scenario(f"values_{rule.name}", rule.description, _rule_seed(rule))
            for rule in RULES.values()
        ],
        Scenario(
            "values_duplicates",
            "a copy of one row of every table, renewing only the unique columns",
            seed_duplicates,
        ),
        Scenario(
            "scale",
            "UPGRADE_CHECK_ROWS sessions, kernels and audit logs and five times as many usage records",
            seed_scale,
        ),
    ]
}


async def _chain(s: Seeder, *seeds: Seed) -> None:
    for seed in seeds:
        await seed(s)


async def _chain_verify(conn: asyncpg.Connection, *verifies: Verify) -> list[str]:
    problems: list[str] = []
    for verify in verifies:
        problems += await verify(conn)
    return problems
