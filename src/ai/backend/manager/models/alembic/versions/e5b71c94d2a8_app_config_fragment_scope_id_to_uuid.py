"""convert app_config_fragments.scope_id to a nullable UUID

``scope_id`` was a ``VARCHAR`` holding a domain or user UUID, with ``''`` for
public only because the column was ``NOT NULL``. It becomes ``UUID NULL``, where
``NULL`` is public.

Public rows are forced to ``NULL``; a domain or user id that is not a UUID aborts
the migration rather than being nulled, since that binding decides who can see
the fragment.

``NULL``s are distinct to a unique constraint, so public rows get a partial
unique index (``UNIQUE NULLS NOT DISTINCT`` needs Postgres 15+; the test fixture
runs 13), and a check constraint keeps ``NULL`` and public in step.

Revision ID: e5b71c94d2a8
Revises: 577c7a215934
Create Date: 2026-07-21

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e5b71c94d2a8"
down_revision = "577c7a215934"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

_PUBLIC_INDEX = "uq_app_config_fragments_public_config_name"
# Bare name — the naming convention prefixes it with ck_<table>_.
_SCOPE_ID_CHECK = "scope_id_matches_scope_type"
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
                    ELSE scope_id::uuid
                END
            )
        """)
    )
    op.create_check_constraint(
        _SCOPE_ID_CHECK,
        _TABLE,
        "(scope_type = 'public') = (scope_id IS NULL)",
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
    op.drop_constraint(_SCOPE_ID_CHECK, _TABLE, type_="check")
    # Public rows go back to the empty sentinel the NOT NULL column required.
    op.execute(
        sa.text("""
            ALTER TABLE app_config_fragments
            ALTER COLUMN scope_id TYPE VARCHAR(255)
            USING (COALESCE(scope_id::text, ''))
        """)
    )
    op.alter_column(_TABLE, "scope_id", nullable=False)
