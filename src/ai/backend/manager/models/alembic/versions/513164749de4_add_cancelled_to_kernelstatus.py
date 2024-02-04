"""add-cancelled-to-kernelstatus

Revision ID: 513164749de4
Revises: 405aa2c39458
Create Date: 2019-09-20 11:13:39.157834

"""

import textwrap

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = "513164749de4"
down_revision = "405aa2c39458"
branch_labels = None
depends_on = None

kernelstatus_new_values = [
    "PENDING",
    "PREPARING",
    "BUILDING",
    "PULLING",
    "RUNNING",
    "RESTARTING",
    "RESIZING",
    "SUSPENDED",
    "TERMINATING",
    "TERMINATED",
    "ERROR",
    "CANCELLED",  # added
]
kernelstatus_new = postgresql.ENUM(*kernelstatus_new_values, name="kernelstatus")

kernelstatus_old_values = [
    "PENDING",
    "PREPARING",
    "BUILDING",
    "PULLING",
    "RUNNING",
    "RESTARTING",
    "RESIZING",
    "SUSPENDED",
    "TERMINATING",
    "TERMINATED",
    # 'ERROR',
]
kernelstatus_old = postgresql.ENUM(*kernelstatus_old_values, name="kernelstatus")


def upgrade():
    conn = op.get_bind()
    conn.execute(text("DROP INDEX IF EXISTS ix_kernels_unique_sess_token;"))
    conn.execute(text("ALTER TYPE kernelstatus RENAME TO kernelstatus_old;"))
    kernelstatus_new.create(conn)
    query = textwrap.dedent(
        """
    ALTER TABLE kernels
        ALTER COLUMN "status" DROP DEFAULT,
        ALTER COLUMN "status" TYPE kernelstatus USING "status"::text::kernelstatus,
        ALTER COLUMN "status" SET DEFAULT 'PENDING'::kernelstatus;
    """
    )
    conn.execute(text(query))
    query = "DROP TYPE kernelstatus_old;"
    conn.execute(text(query))
    op.create_index(
        "ix_kernels_unique_sess_token",
        "kernels",
        ["access_key", "sess_id"],
        unique=True,
        postgresql_where=sa.text("status NOT IN ('TERMINATED', 'CANCELLED') and role = 'master'"),
    )


def downgrade():
    op.drop_index("ix_kernels_unique_sess_token", table_name="kernels")
    conn = op.get_bind()
    conn.execute(text("ALTER TYPE kernelstatus RENAME TO kernelstatus_new;"))
    kernelstatus_old.create(conn)
    conn.execute(
        text(
            textwrap.dedent(
                """\
            ALTER TABLE kernels
                ALTER COLUMN "status" DROP DEFAULT,
                ALTER COLUMN "status" TYPE kernelstatus USING (
                    CASE "status"::text
                        WHEN 'CANCELLED' THEN 'TERMINATED'
                        ELSE "status"::text
                    END
                )::kernelstatus,
                ALTER COLUMN "status" SET DEFAULT 'PREPARING'::kernelstatus;
            """
            )
        )
    )
    conn.execute(text("DROP TYPE kernelstatus_new;"))
    op.create_index(
        "ix_kernels_unique_sess_token",
        "kernels",
        ["access_key", "sess_id"],
        unique=True,
        postgresql_where=sa.text("status != 'TERMINATED' and role = 'master'"),
    )
