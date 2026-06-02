"""migrate_session_app_to_rbac

Revision ID: 3632aad9d5d9
Revises: 6e5a7a62a687
Create Date: 2026-05-01 00:00:01.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision = "3632aad9d5d9"
down_revision = "6e5a7a62a687"
branch_labels = None
depends_on = None

# Part of: 26.5.0

# Constants
MEMBER_ROLE_PATTERN = "%member"
ENTITY_TYPE = "session:app_service"
USER_SCOPE_TYPE = "user"
PROJECT_SCOPE_TYPE = "project"
SESSION_SCOPE_TYPE = "session"
READ_OPERATION = "read"

# Sessions in these terminal/error states no longer expose a usable app
# endpoint, so granting `session:app_service` permissions on them would be
# wasted rows that never resolve at the runtime.
DEAD_SESSION_STATUSES = ["TERMINATING", "TERMINATED", "CANCELLED", "ERROR"]


def _seed_user_session_grants(db_conn: Connection) -> None:
    """Per-entity grants for the session creator.

    For each live session created by user U, grant U's user-scope
    ("system") role read on that specific `session:app_service` via the
    entity-as-scope pattern. Lands in the resolver's self-scope branch
    only — no leak via scope-walker.
    """
    insert_query = sa.text("""
        WITH user_role_sessions AS (
            SELECT DISTINCT
                ur.role_id,
                s.id::text AS session_id
            FROM sessions s
            JOIN user_roles ur ON ur.user_id = s.user_uuid
            JOIN permissions p ON p.role_id = ur.role_id
            WHERE s.status::text <> ALL(CAST(:dead_statuses AS text[]))
              AND p.scope_type = :user_scope
              AND p.scope_id = s.user_uuid::text
        )
        INSERT INTO permissions (role_id, scope_type, scope_id, entity_type, operation)
        SELECT
            urs.role_id,
            :scope_type AS scope_type,
            urs.session_id AS scope_id,
            :entity_type AS entity_type,
            :operation AS operation
        FROM user_role_sessions urs
        ON CONFLICT (role_id, scope_type, scope_id, entity_type, operation) DO NOTHING
    """)
    db_conn.execute(
        insert_query,
        {
            "dead_statuses": DEAD_SESSION_STATUSES,
            "user_scope": USER_SCOPE_TYPE,
            "scope_type": SESSION_SCOPE_TYPE,
            "entity_type": ENTITY_TYPE,
            "operation": READ_OPERATION,
        },
    )


def _seed_project_session_grants(db_conn: Connection) -> None:
    """Per-entity grants for the project's owner/admin roles.

    For each live session in project P (sessions always carry group_id),
    grant P's non-member roles read on that specific `session:app_service`.
    """
    insert_query = sa.text("""
        WITH project_role_sessions AS (
            SELECT DISTINCT
                p.role_id,
                s.id::text AS session_id
            FROM sessions s
            JOIN permissions p
              ON p.scope_type = :project_scope
             AND p.scope_id = s.group_id::text
            JOIN roles r ON r.id = p.role_id
            WHERE s.status::text <> ALL(CAST(:dead_statuses AS text[]))
              AND s.group_id IS NOT NULL
              AND r.name NOT LIKE :member_pattern
        )
        INSERT INTO permissions (role_id, scope_type, scope_id, entity_type, operation)
        SELECT
            prs.role_id,
            :scope_type AS scope_type,
            prs.session_id AS scope_id,
            :entity_type AS entity_type,
            :operation AS operation
        FROM project_role_sessions prs
        ON CONFLICT (role_id, scope_type, scope_id, entity_type, operation) DO NOTHING
    """)
    db_conn.execute(
        insert_query,
        {
            "dead_statuses": DEAD_SESSION_STATUSES,
            "project_scope": PROJECT_SCOPE_TYPE,
            "scope_type": SESSION_SCOPE_TYPE,
            "entity_type": ENTITY_TYPE,
            "operation": READ_OPERATION,
            "member_pattern": MEMBER_ROLE_PATTERN,
        },
    )


def upgrade() -> None:
    conn = op.get_bind()
    _seed_user_session_grants(conn)
    _seed_project_session_grants(conn)


def downgrade() -> None:
    # Intentionally a no-op. Once the runtime starts using `session:app_service`,
    # operators may grant/revoke additional permissions on this entity type.
    # A blanket DELETE WHERE entity_type='session:app_service' would erase those
    # operator-managed rows together with the seed, so this migration is
    # forward-only by design.
    pass
