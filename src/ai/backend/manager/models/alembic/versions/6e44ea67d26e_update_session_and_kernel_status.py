"""update_session_and_kernel_status

Revision ID: 6e44ea67d26e
Revises: 59a622c31820
Create Date: 2024-08-05 14:39:11.901615

"""

import enum

from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = "6e44ea67d26e"
down_revision = "59a622c31820"
branch_labels = None
depends_on = None

KERNEL_STATUS_ENUM_NAME = "kernelstatus"
SESSION_STATUS_ENUM_NAME = "sessionstatus"

NEW_STATUS_NAME = "READY_TO_CREATE"


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
    # Relax the colum type from enum to varchar(64).
    conn.execute(
        text("ALTER TABLE kernels ALTER COLUMN status TYPE varchar(64) USING status::text;")
    )
    conn.execute(
        text("ALTER TABLE sessions ALTER COLUMN status TYPE varchar(64) USING status::text;")
    )
    conn.execute(text(f"DROP TYPE {KERNEL_STATUS_ENUM_NAME};"))
    conn.execute(text(f"DROP TYPE {SESSION_STATUS_ENUM_NAME};"))


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
                WHEN status = '{NEW_STATUS_NAME}' THEN 'SCHEDULED'
                ELSE status
            END,
            status_history = status_history - '{NEW_STATUS_NAME}';
        """
            )
        )
        _values = ",".join(f"'{choice.value}'" for choice in status_enum)
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
