"""update_session_and_kernel_status

Revision ID: 6e44ea67d26e
Revises: d4c174934fd0
Create Date: 2024-08-05 14:39:11.901615

"""

import enum

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = "6e44ea67d26e"
down_revision = "d4c174934fd0"
branch_labels = None
depends_on = None

KERNEL_STATUS_ENUM_NAME = "kernelstatus"
SESSION_STATUS_ENUM_NAME = "sessionstatus"

PREPARED = "PREPARED"


class OldKernelStatus(enum.Enum):
    PENDING = 0
    SCHEDULED = 5
    PREPARING = 10
    BUILDING = 20
    PULLING = 21
    RUNNING = 30
    RESTARTING = 31
    RESIZING = 32
    SUSPENDED = 33
    TERMINATING = 40
    TERMINATED = 41
    ERROR = 42
    CANCELLED = 43


class OldSessionStatus(enum.Enum):
    PENDING = 0
    SCHEDULED = 5
    PULLING = 7
    PREPARING = 10
    RUNNING = 30
    RESTARTING = 31
    RUNNING_DEGRADED = 32
    TERMINATING = 40
    TERMINATED = 41
    ERROR = 42
    CANCELLED = 43


def upgrade() -> None:
    conn = op.get_bind()
    # Drop indexes temporarily
    op.drop_index(op.f("ix_sessions_status"), table_name="sessions")
    op.drop_index(op.f("ix_kernels_status"), table_name="kernels")
    op.drop_index(op.f("ix_kernels_status_role"), table_name="kernels")
    op.drop_index(op.f("ix_kernels_unique_sess_token"), table_name="kernels")

    # Relax the colum type from enum to varchar(64).
    conn.execute(
        text("ALTER TABLE kernels ALTER COLUMN status TYPE VARCHAR(64) USING status::VARCHAR;")
    )
    conn.execute(text("ALTER TABLE kernels ALTER COLUMN status SET DEFAULT 'PENDING';"))
    conn.execute(
        text("ALTER TABLE sessions ALTER COLUMN status TYPE VARCHAR(64) USING status::VARCHAR;")
    )
    conn.execute(text("ALTER TABLE sessions ALTER COLUMN status SET DEFAULT 'PENDING';"))
    conn.execute(text(f"DROP TYPE {KERNEL_STATUS_ENUM_NAME};"))
    conn.execute(text(f"DROP TYPE {SESSION_STATUS_ENUM_NAME};"))

    # Recreate indexes
    op.create_index(op.f("ix_sessions_status"), "sessions", ["status"], unique=False)
    op.create_index(op.f("ix_kernels_status"), "kernels", ["status"], unique=False)


def downgrade() -> None:
    conn = op.get_bind()

    def _remove_new_state_and_create_enum(
        table_name: str, enum_name: str, status_enum: type[enum.Enum]
    ) -> None:
        conn.execute(
            text(
                f"""\
            UPDATE {table_name}
            SET status = CASE
                WHEN status = '{PREPARED}' THEN 'SCHEDULED'
                ELSE status
            END;
        """
            )
        )
        _values = ",".join(f"'{choice.name}'" for choice in status_enum)
        conn.execute(text(f"CREATE TYPE {enum_name} AS ENUM ({_values})"))
        conn.execute(text(f"ALTER TABLE {table_name} ALTER COLUMN status DROP DEFAULT;"))
        conn.execute(
            text(
                f"ALTER TABLE {table_name} ALTER COLUMN status TYPE {enum_name} USING status::{enum_name};"
            )
        )
        conn.execute(text(f"ALTER TABLE {table_name} ALTER COLUMN status SET DEFAULT 'PENDING';"))

    _remove_new_state_and_create_enum("kernels", KERNEL_STATUS_ENUM_NAME, OldKernelStatus)
    _remove_new_state_and_create_enum("sessions", SESSION_STATUS_ENUM_NAME, OldSessionStatus)

    op.create_index("ix_kernels_status_role", "kernels", ["status", "cluster_role"], unique=False)
    op.create_index(
        "ix_kernels_unique_sess_token",
        "kernels",
        ["access_key", "session_name"],
        unique=True,
        postgresql_where=sa.text(
            "status NOT IN ('TERMINATED', 'CANCELLED') and cluster_role = 'main'"
        ),
    )
