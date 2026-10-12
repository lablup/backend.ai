"""add session_groups table and placement group FKs

Introduces ``session_groups``, the holder of the per-agent placement policy of
a set of sessions (BEP-1064). Membership is bound through the two new FKs:
``sessions.session_group_id`` is nullable (NULL means no placement constraint,
the default for ordinary sessions) and indexed because it is the join key of
the scheduler's per-agent membership query, while
``replica_groups.session_group_id`` is NOT NULL — a replica group always owns
exactly one group.

Existing replica groups are backfilled with one group each, taking the
ownership axes from their endpoint's ``(domain, project, session_owner)`` and
the deployment default policy, ``spread`` + ``preferred``. ``preferred`` rather
than ``strict``: nothing enforced replica spreading before, so a strict policy
could turn services that used to deploy fine into placement failures. Their
existing route sessions join the same group so a running deployment's members
are visible to the scheduler from the first tick.

``endpoints.session_owner`` has no FK, and a user purge that delegates ownership skips
non-``created`` deployments, so an owner may be gone. Such a deployment passes to its
``created_user`` when that user remains; one with neither user nor route is removed, as
a purge without delegation removes it.

Revision ID: 8f3c1d5a2b47
Revises: 890490020974
Create Date: 2026-07-28

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "8f3c1d5a2b47"
down_revision = "890490020974"
# Part of: 26.8.0
branch_labels = None
depends_on = None

_OWNER_GONE = "NOT EXISTS (SELECT 1 FROM users u WHERE u.uuid = e.session_owner)"
_CREATOR_LEFT = "EXISTS (SELECT 1 FROM users u WHERE u.uuid = e.created_user)"
_UNOWNED = f"""
    SELECT e.id FROM endpoints e
    WHERE {_OWNER_GONE} AND NOT {_CREATOR_LEFT}
      AND NOT EXISTS (SELECT 1 FROM routings r WHERE r.endpoint = e.id)
"""

REASSIGN_TO_CREATOR_SQL = (
    f"""
UPDATE endpoint_tokens t SET session_owner = e.created_user
FROM endpoints e
WHERE t.endpoint = e.id AND {_OWNER_GONE} AND {_CREATOR_LEFT}
""",
    f"""
UPDATE endpoints e SET session_owner = e.created_user
WHERE {_OWNER_GONE} AND {_CREATOR_LEFT}
""",
)

# Replica groups and policies go with the endpoint by FK cascade.
REMOVE_UNOWNED_SQL = (
    f"DELETE FROM endpoint_tokens WHERE endpoint IN ({_UNOWNED})",
    f"DELETE FROM endpoints WHERE id IN ({_UNOWNED})",
)

# One session group per existing replica group, in a single statement: the
# ``new_groups`` CTE holds the generated ids so the INSERT and the UPDATE agree
# on them. Re-running is a no-op thanks to the ``session_group_id IS NULL``
# guard.
BACKFILL_SQL = """
WITH new_groups AS (
    SELECT
        rg.id AS replica_group_id,
        uuid_generate_v4() AS session_group_id,
        d.id AS domain_id,
        e.project AS project_id,
        e.session_owner AS owner_user_id
    FROM replica_groups rg
    JOIN endpoints e ON e.id = rg.deployment_id
    JOIN domains d ON d.name = e.domain
    WHERE rg.session_group_id IS NULL
), inserted AS (
    INSERT INTO session_groups (
        id, domain_id, project_id, owner_user_id,
        placement_direction, placement_enforcement
    )
    SELECT
        session_group_id, domain_id, project_id, owner_user_id,
        'spread', 'preferred'
    FROM new_groups
)
UPDATE replica_groups rg
SET session_group_id = ng.session_group_id
FROM new_groups ng
WHERE rg.id = ng.replica_group_id
"""

# The route sessions of a replica group are its group's members, so existing
# ones join the group their route belongs to. Without this the scheduler sees
# no members for a group whose replicas are already running. Runs after the
# replica group backfill above, which is where the group ids come from.
BACKFILL_ROUTE_SESSIONS_SQL = """
UPDATE sessions s
SET session_group_id = rg.session_group_id
FROM routings r
JOIN replica_groups rg ON rg.id = r.replica_group_id
WHERE r.session = s.id
  AND s.session_group_id IS NULL
"""


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "session_groups" not in inspector.get_table_names():
        op.create_table(
            "session_groups",
            sa.Column("id", GUID, nullable=False, server_default=sa.text("uuid_generate_v4()")),
            sa.Column("domain_id", GUID, nullable=False),
            sa.Column("project_id", GUID, nullable=False),
            sa.Column("owner_user_id", GUID, nullable=False),
            sa.Column("placement_direction", sa.String(length=64), nullable=False),
            sa.Column("placement_enforcement", sa.String(length=64), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(
                ["domain_id"], ["domains.id"], name="fk_session_groups_domain_id_domains"
            ),
            sa.ForeignKeyConstraint(
                ["project_id"], ["groups.id"], name="fk_session_groups_project_id_groups"
            ),
            sa.ForeignKeyConstraint(
                ["owner_user_id"],
                ["users.uuid"],
                name="fk_session_groups_owner_user_id_users",
                ondelete="RESTRICT",
            ),
            sa.PrimaryKeyConstraint("id", name="pk_session_groups"),
        )

    session_columns = {c["name"] for c in inspector.get_columns("sessions")}
    if "session_group_id" not in session_columns:
        op.add_column("sessions", sa.Column("session_group_id", GUID, nullable=True))
        op.create_foreign_key(
            "fk_sessions_session_group_id_session_groups",
            "sessions",
            "session_groups",
            ["session_group_id"],
            ["id"],
            ondelete="SET NULL",
        )
    session_indexes = {i["name"] for i in inspector.get_indexes("sessions")}
    if "ix_sessions_session_group_id" not in session_indexes:
        op.create_index("ix_sessions_session_group_id", "sessions", ["session_group_id"])

    replica_group_columns = {c["name"] for c in inspector.get_columns("replica_groups")}
    if "session_group_id" not in replica_group_columns:
        op.add_column("replica_groups", sa.Column("session_group_id", GUID, nullable=True))
        op.create_foreign_key(
            "fk_replica_groups_session_group_id_session_groups",
            "replica_groups",
            "session_groups",
            ["session_group_id"],
            ["id"],
        )

    for statement in (*REASSIGN_TO_CREATOR_SQL, *REMOVE_UNOWNED_SQL):
        op.execute(statement)
    op.execute(BACKFILL_SQL)
    op.alter_column("replica_groups", "session_group_id", nullable=False)
    op.execute(BACKFILL_ROUTE_SESSIONS_SQL)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_sessions_session_group_id")
    op.execute("ALTER TABLE sessions DROP COLUMN IF EXISTS session_group_id")
    op.execute("ALTER TABLE replica_groups DROP COLUMN IF EXISTS session_group_id")
    op.execute("DROP TABLE IF EXISTS session_groups")
