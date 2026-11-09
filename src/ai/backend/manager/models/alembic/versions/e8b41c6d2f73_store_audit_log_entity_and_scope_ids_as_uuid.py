"""store audit log entity and scope ids as uuid

Revision ID: e8b41c6d2f73
Revises: f7b1e5a9032c
Create Date: 2026-10-06

"""

import sqlalchemy as sa
from alembic import op

# Part of: NEXT_RELEASE_VERSION

# revision identifiers, used by Alembic.
revision = "e8b41c6d2f73"
down_revision = "f7b1e5a9032c"
branch_labels = None
depends_on = None

_UUID_PATTERN = "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"


def _column_type(table: str, column: str) -> str | None:
    return (
        op.get_bind()
        .execute(
            sa.text(
                "SELECT data_type FROM information_schema.columns "
                "WHERE table_name = :table AND column_name = :column"
            ),
            {"table": table, "column": column},
        )
        .scalar()
    )


def upgrade() -> None:
    # A value that is not a uuid names no entity; it is dropped rather than kept.
    if _column_type("audit_logs", "entity_id") != "uuid":
        op.execute(
            sa.text(
                "UPDATE audit_logs SET entity_id = NULL WHERE entity_id !~ :pattern"
            ).bindparams(pattern=_UUID_PATTERN)
        )
        op.execute(
            sa.text("ALTER TABLE audit_logs ALTER COLUMN entity_id TYPE uuid USING entity_id::uuid")
        )
    if _column_type("audit_log_scopes", "scope_id") != "uuid":
        op.execute(
            sa.text("DELETE FROM audit_log_scopes WHERE scope_id !~ :pattern").bindparams(
                pattern=_UUID_PATTERN
            )
        )
        op.execute(
            sa.text(
                "ALTER TABLE audit_log_scopes ALTER COLUMN scope_id TYPE uuid USING scope_id::uuid"
            )
        )


def downgrade() -> None:
    if _column_type("audit_log_scopes", "scope_id") == "uuid":
        op.execute(
            sa.text(
                "ALTER TABLE audit_log_scopes ALTER COLUMN scope_id TYPE varchar USING scope_id::text"
            )
        )
    if _column_type("audit_logs", "entity_id") == "uuid":
        op.execute(
            sa.text(
                "ALTER TABLE audit_logs ALTER COLUMN entity_id TYPE varchar USING entity_id::text"
            )
        )
