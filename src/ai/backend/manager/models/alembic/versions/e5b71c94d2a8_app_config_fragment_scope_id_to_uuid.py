"""convert app_config_fragments.scope_id to a nullable UUID

``scope_id`` held a ``VARCHAR(255)`` that was never really a string: a domain
fragment stores a domain id and a user fragment a user id, both UUIDs, while a
public fragment has no owner at all and stored ``''`` only because the column
was ``NOT NULL``. Store the real type instead — ``UUID NULL``, with ``NULL``
meaning "public, no owner".

The uniqueness of ``(config_name, scope_type, scope_id)`` needs help: Postgres
treats ``NULL``s as distinct in a unique constraint, so the existing constraint
stops rejecting a second public fragment for the same config name once public
rows hold ``NULL``. A partial unique index over the ``NULL`` rows restores the
guarantee the ``''`` sentinel used to provide. (``UNIQUE NULLS NOT DISTINCT``
would say the same thing in one constraint, but it needs Postgres 15+ and the
test fixture runs 13.)

Public rows are forced to ``NULL`` regardless of what they stored, since public
has no owner by definition. Domain and user rows are cast, and a value that is
not a UUID fails the migration on purpose — nulling it would silently drop the
scope binding that decides who can see the fragment.

Revision ID: e5b71c94d2a8
Revises: c7e2b48a15d9
Create Date: 2026-07-21

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e5b71c94d2a8"
down_revision = "c7e2b48a15d9"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

_PUBLIC_INDEX = "uq_app_config_fragments_public_config_name"
_TABLE = "app_config_fragments"


def upgrade() -> None:
    op.execute(
        sa.text("""
            ALTER TABLE app_config_fragments
            ALTER COLUMN scope_id DROP NOT NULL,
            ALTER COLUMN scope_id TYPE UUID
            USING (
                CASE
                    WHEN scope_type = 'public' THEN NULL
                    ELSE NULLIF(scope_id, '')::uuid
                END
            )
        """)
    )
    op.create_index(
        _PUBLIC_INDEX,
        _TABLE,
        ["config_name", "scope_type"],
        unique=True,
        postgresql_where=sa.text("scope_id IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(_PUBLIC_INDEX, table_name=_TABLE)
    # Public rows go back to the empty sentinel the NOT NULL column used to require, which
    # the plain constraint can compare like any other value.
    op.execute(
        sa.text("""
            ALTER TABLE app_config_fragments
            ALTER COLUMN scope_id TYPE VARCHAR(255)
            USING (COALESCE(scope_id::text, ''))
        """)
    )
    op.alter_column(_TABLE, "scope_id", nullable=False)
