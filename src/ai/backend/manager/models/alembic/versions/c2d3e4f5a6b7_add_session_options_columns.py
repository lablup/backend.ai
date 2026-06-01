"""add session options JSONB columns

Introduces the session-side counterparts of ``default_deployment_options``
/ ``endpoints.options`` (added in ``b1a2c3d4e5f6``):

1. ``scaling_groups.default_session_options`` (jsonb, NOT NULL) —
   baseline session options that the create-session resolver falls
   back to when a request omits fields. Snapshot into each session at
   enqueue time so later scaling-group tweaks do not retroactively
   alter live sessions.
2. ``sessions.options`` (jsonb, NOT NULL) — subset of the resolved
   :class:`SessionOptions` that does not already live in a dedicated
   ``SessionRow`` column (``kernel_groups``, ``timeouts``,
   ``agent_selection_policy``). Existing columns (``priority``,
   ``is_preemptible``, ``cluster_mode``, ``cluster_size``,
   ``scaling_group_name``, ``designated_agent_ids``) keep carrying the
   rest so pre-existing SQL filters keep working unchanged.

Existing rows are backfilled with the empty-defaults JSON emitted by
``DefaultSessionOptions()`` / ``SessionStoredOptions()``. Downgrade
drops both columns.

Revision ID: c2d3e4f5a6b7
Revises: b1a2c3d4e5f6
Create Date: 2026-04-22

"""

# Part of: 26.5.0

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgsql

# revision identifiers, used by Alembic.
revision = "c2d3e4f5a6b7"
down_revision = "b1a2c3d4e5f6"
branch_labels = None
depends_on = None


# Emitted by ``DefaultSessionOptions().model_dump_json()`` — keep in
# sync with ``manager.data.session.options.DefaultSessionOptions``
# defaults.
_DEFAULT_SESSION_OPTIONS_JSON = (
    "{"
    '"priority":10,'
    '"is_preemptible":true,'
    '"cluster_mode":"single-node",'
    '"default_failure_policy":"strict",'
    '"default_kernel_execution_spec":null,'
    '"timeouts":{"default":null,"by_handler":{}},'
    '"agent_selection_policy":"preferred"'
    "}"
)

# Emitted by ``SessionStoredOptions().model_dump_json()``.
_SESSION_STORED_OPTIONS_JSON = (
    "{"
    '"kernel_groups":[],'
    '"timeouts":{"default":null,"by_handler":{}},'
    '"agent_selection_policy":"preferred"'
    "}"
)


def _add_jsonb_column_with_default(table: str, column: str, default_json: str) -> None:
    """Add a JSONB column with a baseline default payload.

    ``ALTER TABLE ... SET DEFAULT`` cannot accept bind parameters, and
    SQLAlchemy's ``text()`` scans rendered SQL for ``:name``
    placeholders even inside quoted literals. Each ``:`` in the JSON
    payload and the ``::jsonb`` cast is therefore escaped with ``\\:``
    so SQLAlchemy emits a literal colon. Mirrors the helper used in
    ``b1a2c3d4e5f6``.
    """
    op.add_column(table, sa.Column(column, pgsql.JSONB(), nullable=True))
    op.execute(
        sa.text(f"UPDATE {table} SET {column} = CAST(:val AS JSONB)").bindparams(val=default_json)
    )
    op.alter_column(table, column, nullable=False)
    escaped_json = default_json.replace(":", r"\:")
    op.execute(
        sa.text(
            f"ALTER TABLE {table} ALTER COLUMN {column} SET DEFAULT '{escaped_json}'\\:\\:jsonb"
        )
    )


def upgrade() -> None:
    _add_jsonb_column_with_default(
        "scaling_groups", "default_session_options", _DEFAULT_SESSION_OPTIONS_JSON
    )
    _add_jsonb_column_with_default("sessions", "options", _SESSION_STORED_OPTIONS_JSON)


def downgrade() -> None:
    op.drop_column("sessions", "options")
    op.drop_column("scaling_groups", "default_session_options")
