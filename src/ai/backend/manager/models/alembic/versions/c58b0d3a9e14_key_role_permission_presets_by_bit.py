"""Key role permission presets by the permission bit

``role_permission_presets.operation`` held an ``OperationType`` string while the
``permissions`` rows it instantiates hold a ``Permission`` bitmask. One preset entry
still means one operation, so the string is replaced by the bit it maps to.

Grant operations carry no bit. No preset holds one -- they were never grantable
through a preset -- so such a row is dropped rather than mapped to an empty mask.

Create Date: 2026-09-10

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c58b0d3a9e14"
down_revision = "a7e4d1f0c832"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

_TABLE = "role_permission_presets"
_CONSTRAINT = "uq_role_permission_presets_preset_entity_op"

# Permission bits, as ``Permission`` numbers them.
_OPERATION_TO_BIT = {
    "read": 1,
    "update": 2,
    "create": 4,
    "soft-delete": 8,
    "hard-delete": 16,
}
_BIT_TO_OPERATION = {bit: operation for operation, bit in _OPERATION_TO_BIT.items()}


def upgrade() -> None:
    op.drop_constraint(_CONSTRAINT, _TABLE, type_="unique")
    op.add_column(_TABLE, sa.Column("permission", sa.Integer(), nullable=True))
    for operation, bit in _OPERATION_TO_BIT.items():
        op.execute(
            sa.text(
                f"UPDATE {_TABLE} SET permission = :bit WHERE operation = :operation"
            ).bindparams(bit=bit, operation=operation)
        )
    # A grant operation has no bit; the entry granted nothing that survives the move.
    op.execute(sa.text(f"DELETE FROM {_TABLE} WHERE permission IS NULL"))
    op.alter_column(_TABLE, "permission", nullable=False)
    op.drop_column(_TABLE, "operation")
    op.create_unique_constraint(
        _CONSTRAINT, _TABLE, ["role_preset_id", "entity_type", "permission"]
    )


def downgrade() -> None:
    op.drop_constraint(_CONSTRAINT, _TABLE, type_="unique")
    op.add_column(_TABLE, sa.Column("operation", sa.String(length=32), nullable=True))
    for bit, operation in _BIT_TO_OPERATION.items():
        op.execute(
            sa.text(
                f"UPDATE {_TABLE} SET operation = :operation WHERE permission = :bit"
            ).bindparams(bit=bit, operation=operation)
        )
    op.execute(sa.text(f"DELETE FROM {_TABLE} WHERE operation IS NULL"))
    op.alter_column(_TABLE, "operation", nullable=False)
    op.drop_column(_TABLE, "permission")
    op.create_unique_constraint(_CONSTRAINT, _TABLE, ["role_preset_id", "entity_type", "operation"])
