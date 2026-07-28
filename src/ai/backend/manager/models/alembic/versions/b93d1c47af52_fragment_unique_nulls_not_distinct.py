"""key app_config_fragments with UNIQUE NULLS NOT DISTINCT

A public fragment has a ``NULL`` scope_id, and ``NULL``s are distinct to a plain
unique constraint, so public rows needed a partial unique index of their own. That
left the table with two arbiter indexes, and every upsert had to pick between them
by scope kind.

``UNIQUE NULLS NOT DISTINCT`` (Postgres 15+, and the product requires 16+) keys the
public row like any other, so the partial index goes away and one conflict target
serves every scope.

Revision ID: b93d1c47af52
Revises: c4a91d7e05b2
Create Date: 2026-07-28

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b93d1c47af52"
down_revision = "c4a91d7e05b2"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

_TABLE = "app_config_fragments"
_UNIQUE = "uq_app_config_fragments_config_name_scope_type_scope_id"
_PUBLIC_INDEX = "uq_app_config_fragments_public_config_name"


def upgrade() -> None:
    # The partial index already kept public rows unique, so nothing can collide under the
    # widened constraint.
    op.execute(sa.text(f"DROP INDEX IF EXISTS {_PUBLIC_INDEX}"))
    op.execute(sa.text(f"ALTER TABLE {_TABLE} DROP CONSTRAINT IF EXISTS {_UNIQUE}"))
    op.execute(
        sa.text(f"""
            ALTER TABLE {_TABLE}
            ADD CONSTRAINT {_UNIQUE}
            UNIQUE NULLS NOT DISTINCT (config_name, scope_type, scope_id)
        """)
    )


def downgrade() -> None:
    op.execute(sa.text(f"ALTER TABLE {_TABLE} DROP CONSTRAINT IF EXISTS {_UNIQUE}"))
    op.execute(
        sa.text(f"""
            ALTER TABLE {_TABLE}
            ADD CONSTRAINT {_UNIQUE}
            UNIQUE (config_name, scope_type, scope_id)
        """)
    )
    # Public rows fall outside the plain constraint again, so restore their own index. A
    # duplicate public row cannot exist here: NULLS NOT DISTINCT rejected it.
    op.execute(
        sa.text(f"""
            CREATE UNIQUE INDEX IF NOT EXISTS {_PUBLIC_INDEX}
            ON {_TABLE} (config_name, scope_type)
            WHERE scope_id IS NULL
        """)
    )
