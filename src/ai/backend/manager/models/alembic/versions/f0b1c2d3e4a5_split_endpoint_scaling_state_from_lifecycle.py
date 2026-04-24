"""split endpoint scaling_state out of EndpointLifecycle

Splits the orthogonal "replica reconciliation in progress" flag off the
:class:`EndpointLifecycle` column into a dedicated ``scaling_state``
column, and adds a :class:`DeploymentHandlerCategory` column on
``deployment_history`` so scaling vs lifecycle (vs future health) work
is distinguishable in history queries.

Upgrade steps:

1. Add ``endpoints.scaling_state`` (varchar(64), NOT NULL, default
   ``'stable'``) — mirrors :class:`StrEnumType` storage.
2. Convert ``endpoints.lifecycle_stage`` from the native
   ``endpointlifecycle`` ENUM to ``varchar(64)`` (aligns with the
   :class:`StrEnumType` replacement for the deprecated
   :class:`EnumValueType`). The native type is dropped so the column
   becomes a plain text column.
3. Backfill legacy lifecycle values:
   * ``lifecycle_stage='scaling'`` → ``(lifecycle_stage='ready',
     scaling_state='scaling')`` (the scaling dimension is the only
     information the legacy row carried).
   * ``lifecycle_stage='created'`` → ``lifecycle_stage='ready'``
     (``created`` was a legacy alias for ``ready`` already treated
     identically at the service boundary).
4. Add ``deployment_history.handler_category`` (varchar(32), NOT NULL,
   default ``'lifecycle'``) so existing rows classify as LIFECYCLE by
   default; new rows get an explicit value from the handler's
   ``category()``.

Downgrade steps reverse the above, re-creating the native
``endpointlifecycle`` ENUM with its original value set so legacy code
that still expects the native type continues to work.

Revision ID: f0b1c2d3e4a5
Revises: e9f0a1b2c3d4
Create Date: 2026-04-20

"""

# Part of: 26.5.0

from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = "f0b1c2d3e4a5"
down_revision = "e9f0a1b2c3d4"
branch_labels = None
depends_on = None


_LIFECYCLE_ENUM = "endpointlifecycle"
_ACTIVE_NAME_INDEX = "ix_endpoints_unique_name_when_active"
_LEGACY_LIFECYCLE_VALUES = (
    "pending",
    "created",
    "scaling",
    "ready",
    "deploying",
    "destroying",
    "destroyed",
)


def upgrade() -> None:
    conn = op.get_bind()

    # 1. endpoints.scaling_state column
    conn.execute(
        text(
            "ALTER TABLE endpoints "
            "ADD COLUMN IF NOT EXISTS scaling_state varchar(64) "
            "NOT NULL DEFAULT 'stable';"
        )
    )

    # 2. The partial unique index on (name, domain, project) references
    #    the native enum in its WHERE predicate, so it must be dropped
    #    before we can drop the type. Re-created further down with a
    #    text-based predicate.
    conn.execute(text(f"DROP INDEX IF EXISTS {_ACTIVE_NAME_INDEX};"))

    # 3. endpoints.lifecycle_stage: native ENUM → varchar(64)
    conn.execute(text("ALTER TABLE endpoints ALTER COLUMN lifecycle_stage DROP DEFAULT;"))
    conn.execute(
        text(
            "ALTER TABLE endpoints "
            "ALTER COLUMN lifecycle_stage TYPE varchar(64) "
            "USING lifecycle_stage::text;"
        )
    )
    conn.execute(text("ALTER TABLE endpoints ALTER COLUMN lifecycle_stage SET DEFAULT 'pending';"))
    conn.execute(text(f"DROP TYPE IF EXISTS {_LIFECYCLE_ENUM};"))

    # 4. Data migration: fold legacy lifecycle values onto the new split.
    conn.execute(
        text(
            "UPDATE endpoints "
            "SET lifecycle_stage = 'ready', scaling_state = 'scaling' "
            "WHERE lifecycle_stage = 'scaling';"
        )
    )
    conn.execute(
        text("UPDATE endpoints SET lifecycle_stage = 'ready' WHERE lifecycle_stage = 'created';")
    )

    # 5. Re-create the partial unique index with a text predicate.
    conn.execute(
        text(
            f"CREATE UNIQUE INDEX {_ACTIVE_NAME_INDEX} "
            "ON endpoints (name, domain, project) "
            "WHERE lifecycle_stage NOT IN ('destroying', 'destroyed');"
        )
    )

    # 6. deployment_history.handler_category column
    conn.execute(
        text(
            "ALTER TABLE deployment_history "
            "ADD COLUMN IF NOT EXISTS handler_category varchar(32) "
            "NOT NULL DEFAULT 'lifecycle';"
        )
    )


def downgrade() -> None:
    conn = op.get_bind()

    # Reverse 6. deployment_history.handler_category
    conn.execute(text("ALTER TABLE deployment_history DROP COLUMN IF EXISTS handler_category;"))

    # Reverse 5. Drop the text-predicate index; re-created with the
    # enum-based predicate after the column type is converted back.
    conn.execute(text(f"DROP INDEX IF EXISTS {_ACTIVE_NAME_INDEX};"))

    # Reverse 4. Rebuild legacy lifecycle values before we re-narrow the
    # column type. Rows that carry ``scaling_state='scaling'`` are
    # projected back onto the legacy ``lifecycle_stage='scaling'`` bucket
    # so a rollback does not silently change the observed status.
    conn.execute(
        text("UPDATE endpoints SET lifecycle_stage = 'scaling' WHERE scaling_state = 'scaling';")
    )
    # ``created`` had no surviving source of truth after the upgrade
    # (both created and ready were stored as 'ready'); leave them as
    # 'ready' on downgrade — the service layer already treats the two
    # values identically.

    # Reverse 3. varchar → native ENUM.
    conn.execute(
        text(
            f"CREATE TYPE {_LIFECYCLE_ENUM} AS ENUM ("
            + ", ".join(f"'{v}'" for v in _LEGACY_LIFECYCLE_VALUES)
            + ");"
        )
    )
    conn.execute(text("ALTER TABLE endpoints ALTER COLUMN lifecycle_stage DROP DEFAULT;"))
    conn.execute(
        text(
            "ALTER TABLE endpoints "
            f"ALTER COLUMN lifecycle_stage TYPE {_LIFECYCLE_ENUM} "
            f"USING lifecycle_stage::{_LIFECYCLE_ENUM};"
        )
    )
    conn.execute(text("ALTER TABLE endpoints ALTER COLUMN lifecycle_stage SET DEFAULT 'pending';"))

    # Reverse 2. Re-create the partial unique index with the original
    # enum-typed predicate.
    conn.execute(
        text(
            f"CREATE UNIQUE INDEX {_ACTIVE_NAME_INDEX} "
            "ON endpoints (name, domain, project) "
            "WHERE lifecycle_stage <> ALL ("
            f"ARRAY['destroying'::{_LIFECYCLE_ENUM}, 'destroyed'::{_LIFECYCLE_ENUM}]);"
        )
    )

    # Reverse 1. scaling_state column
    conn.execute(text("ALTER TABLE endpoints DROP COLUMN IF EXISTS scaling_state;"))
