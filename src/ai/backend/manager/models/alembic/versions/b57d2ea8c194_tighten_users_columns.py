"""tighten the always-populated users columns

Six columns are nullable in the schema while every write path sets them, so
readers carry a ``None`` branch that cannot be taken — ``role`` in particular,
which the auth path had to reject a user for lacking.

Left nullable on purpose: ``full_name``, ``description``, ``integration_id``,
``allowed_client_ip``, ``totp_key``, ``totp_activated_at`` and the container id
columns are genuinely optional; ``status_info`` defaults to NULL in the model
itself; ``password`` may legitimately be absent for accounts an auth plugin
owns; ``domain_name`` and ``domain_id`` are mid-transition under BA-7158.

Revision ID: b57d2ea8c194
Revises: e4a91c05df38
Create Date: 2026-08-06 13:50:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b57d2ea8c194"
down_revision = "e4a91c05df38"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

_TIGHTENED = (
    "need_password_change",
    "password_changed_at",
    "created_at",
    "modified_at",
    "role",
    "totp_activated",
)


def upgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text("UPDATE users SET need_password_change = false WHERE need_password_change IS NULL")
    )
    bind.execute(
        sa.text("UPDATE users SET password_changed_at = now() WHERE password_changed_at IS NULL")
    )
    bind.execute(sa.text("UPDATE users SET created_at = now() WHERE created_at IS NULL"))
    bind.execute(sa.text("UPDATE users SET modified_at = now() WHERE modified_at IS NULL"))
    bind.execute(sa.text("UPDATE users SET role = 'user' WHERE role IS NULL"))
    bind.execute(sa.text("UPDATE users SET totp_activated = false WHERE totp_activated IS NULL"))

    for column in _TIGHTENED:
        op.alter_column("users", column, nullable=False)


def downgrade() -> None:
    for column in _TIGHTENED:
        op.alter_column("users", column, nullable=True)
