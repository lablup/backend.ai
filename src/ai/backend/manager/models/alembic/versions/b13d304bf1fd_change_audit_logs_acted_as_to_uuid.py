"""change audit_logs.acted_as to uuid

``acted_as`` is always a user UUID or NULL (the monitor writes ``current_user().user_id``
or ``None``, and existing rows were backfilled from ``triggered_by`` which is a user UUID).
Retype the column from ``String`` to native ``UUID`` so the DB type matches the value it
already holds and the exposed type. ``triggered_by`` intentionally stays ``String``.

Existing text values are valid UUID strings, so the cast is total; NULLs stay NULL.

Revision ID: b13d304bf1fd
Revises: a3c1d8e5b294
Create Date: 2026-07-13

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "b13d304bf1fd"
down_revision = "a3c1d8e5b294"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "audit_logs",
        "acted_as",
        existing_type=sa.String(),
        type_=postgresql.UUID(as_uuid=True),
        existing_nullable=True,
        postgresql_using="acted_as::uuid",
    )


def downgrade() -> None:
    op.alter_column(
        "audit_logs",
        "acted_as",
        existing_type=postgresql.UUID(as_uuid=True),
        type_=sa.String(),
        existing_nullable=True,
        postgresql_using="acted_as::text",
    )
