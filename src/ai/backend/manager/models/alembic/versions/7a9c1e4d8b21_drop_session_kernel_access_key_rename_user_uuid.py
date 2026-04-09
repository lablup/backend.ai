"""drop sessions/kernels access_key and rename user_uuid to owner_id

Phase A of BA-5609: introduce ``owner_id`` as the canonical owner key on the
``sessions`` and ``kernels`` tables. The legacy ``access_key`` column is removed
entirely; downstream code is migrated to resolve ``main_access_key`` from the
owning user when needed.

Revision ID: 7a9c1e4d8b21
Revises: 689f66507280
Create Date: 2026-04-08

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "7a9c1e4d8b21"
down_revision = "99805291b6e0"
# Part of: 26.3.0
branch_labels = None
depends_on = None


_PARTIAL_UNIQUE_NAME_OLD = "ix_sessions_unique_name_per_user_nonterminal"


def _column_names(inspector: sa.engine.reflection.Inspector, table: str) -> set[str]:
    return {c["name"] for c in inspector.get_columns(table)}


def _index_names(inspector: sa.engine.reflection.Inspector, table: str) -> set[str]:
    return {ix["name"] for ix in inspector.get_indexes(table) if ix["name"] is not None}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # ---- sessions ----
    sess_cols = _column_names(inspector, "sessions")
    sess_idxs = _index_names(inspector, "sessions")

    # Drop the partial unique index that references user_uuid before renaming.
    if _PARTIAL_UNIQUE_NAME_OLD in sess_idxs:
        op.drop_index(_PARTIAL_UNIQUE_NAME_OLD, table_name="sessions")

    if "access_key" in sess_cols:
        # Drop any auto-generated index on access_key if present.
        for ix_name in list(sess_idxs):
            if ix_name and "access_key" in ix_name:
                op.drop_index(ix_name, table_name="sessions")
        op.drop_column("sessions", "access_key")

    # Rename user_uuid -> owner_id (refresh column set after potential drop).
    sess_cols = _column_names(inspector, "sessions")
    if "user_uuid" in sess_cols and "owner_id" not in sess_cols:
        op.alter_column("sessions", "user_uuid", new_column_name="owner_id")

    # Recreate the partial unique index using owner_id.
    sess_idxs = _index_names(inspector, "sessions")
    if "ix_sessions_unique_name_per_owner_nonterminal" not in sess_idxs:
        op.create_index(
            "ix_sessions_unique_name_per_owner_nonterminal",
            "sessions",
            ["name", "owner_id"],
            unique=True,
            postgresql_where=sa.text("status NOT IN ('ERROR', 'TERMINATED', 'CANCELLED')"),
        )

    # ---- kernels ----
    kern_cols = _column_names(inspector, "kernels")
    kern_idxs = _index_names(inspector, "kernels")

    if "access_key" in kern_cols:
        for ix_name in list(kern_idxs):
            if ix_name and "access_key" in ix_name:
                op.drop_index(ix_name, table_name="kernels")
        op.drop_column("kernels", "access_key")

    kern_cols = _column_names(inspector, "kernels")
    if "user_uuid" in kern_cols and "owner_id" not in kern_cols:
        op.alter_column("kernels", "user_uuid", new_column_name="owner_id")


def downgrade() -> None:
    """Reverse the rename and recreate access_key columns.

    NOTE: This downgrade is intentionally lossy. The previous values of
    ``sessions.access_key`` and ``kernels.access_key`` cannot be restored
    because the upgrade does not preserve them. The columns are recreated
    as nullable so the schema shape matches, but no backfill is performed.
    """
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # ---- kernels ----
    kern_cols = _column_names(inspector, "kernels")
    if "owner_id" in kern_cols and "user_uuid" not in kern_cols:
        op.alter_column("kernels", "owner_id", new_column_name="user_uuid")

    kern_cols = _column_names(inspector, "kernels")
    if "access_key" not in kern_cols:
        op.add_column(
            "kernels",
            sa.Column("access_key", sa.String(length=20), nullable=True),
        )

    # ---- sessions ----
    sess_idxs = _index_names(inspector, "sessions")
    if "ix_sessions_unique_name_per_owner_nonterminal" in sess_idxs:
        op.drop_index("ix_sessions_unique_name_per_owner_nonterminal", table_name="sessions")

    sess_cols = _column_names(inspector, "sessions")
    if "owner_id" in sess_cols and "user_uuid" not in sess_cols:
        op.alter_column("sessions", "owner_id", new_column_name="user_uuid")

    sess_cols = _column_names(inspector, "sessions")
    if "access_key" not in sess_cols:
        op.add_column(
            "sessions",
            sa.Column("access_key", sa.String(length=20), nullable=True),
        )

    sess_idxs = _index_names(inspector, "sessions")
    if _PARTIAL_UNIQUE_NAME_OLD not in sess_idxs:
        op.create_index(
            _PARTIAL_UNIQUE_NAME_OLD,
            "sessions",
            ["name", "user_uuid"],
            unique=True,
            postgresql_where=sa.text("status NOT IN ('ERROR', 'TERMINATED', 'CANCELLED')"),
        )
