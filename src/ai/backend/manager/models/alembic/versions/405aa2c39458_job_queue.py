"""job-queue

Revision ID: 405aa2c39458
Revises: 5b45f28d2cac
Create Date: 2019-09-16 02:08:41.396372

"""

import textwrap

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import text

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "405aa2c39458"
down_revision = "5b45f28d2cac"
branch_labels = None
depends_on = None

sessionresult = postgresql.ENUM("UNDEFINED", "SUCCESS", "FAILURE", name="sessionresult")

sessiontypes = postgresql.ENUM("INTERACTIVE", "BATCH", name="sessiontypes")

kernelstatus_new_values = [
    "PENDING",  # added
    "PREPARING",
    "BUILDING",
    "PULLING",  # added
    "RUNNING",
    "RESTARTING",
    "RESIZING",
    "SUSPENDED",
    "TERMINATING",
    "TERMINATED",
    "ERROR",
]
kernelstatus_new = postgresql.ENUM(*kernelstatus_new_values, name="kernelstatus")

kernelstatus_old_values = [
    # 'PENDING',     # added
    "PREPARING",
    "BUILDING",
    # 'PULLING',     # added
    "RUNNING",
    "RESTARTING",
    "RESIZING",
    "SUSPENDED",
    "TERMINATING",
    "TERMINATED",
    "ERROR",
]
kernelstatus_old = postgresql.ENUM(*kernelstatus_old_values, name="kernelstatus")


def upgrade():
    conn = op.get_bind()
    sessionresult.create(conn)
    sessiontypes.create(conn)
    conn.execute(text("ALTER TYPE kernelstatus RENAME TO kernelstatus_old;"))
    kernelstatus_new.create(conn)
    query = """
    CREATE FUNCTION kernelstatus_new_old_compare(
        new_enum_val kernelstatus, old_enum_val kernelstatus_old
    )
        RETURNS boolean AS $$
            SELECT new_enum_val::text <> old_enum_val::text;
        $$ LANGUAGE SQL IMMUTABLE;
    """
    conn.execute(text(query))
    queries = textwrap.dedent(
        """
    CREATE OPERATOR <> (
        leftarg = kernelstatus,
        rightarg = kernelstatus_old,
        procedure = kernelstatus_new_old_compare
    );

    ALTER TABLE kernels
        ALTER COLUMN "status" DROP DEFAULT,
        ALTER COLUMN "status" TYPE kernelstatus USING "status"::text::kernelstatus,
        ALTER COLUMN "status" SET DEFAULT 'PENDING'::kernelstatus;

    DROP FUNCTION kernelstatus_new_old_compare(
        new_enum_val kernelstatus, old_enum_val kernelstatus_old
    ) CASCADE;

    DROP TYPE kernelstatus_old;
    """
    )
    for query in queries.split(";"):
        if len(query.strip()) == 0:
            continue
        conn.execute(text(query))

    op.add_column("agents", sa.Column("status_changed", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "kernel_dependencies",
        sa.Column("kernel_id", GUID(), nullable=False),
        sa.Column("depends_on", GUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["depends_on"], ["kernels.id"], name=op.f("fk_kernel_dependencies_depends_on_kernels")
        ),
        sa.ForeignKeyConstraint(
            ["kernel_id"], ["kernels.id"], name=op.f("fk_kernel_dependencies_kernel_id_kernels")
        ),
        sa.PrimaryKeyConstraint("kernel_id", "depends_on", name=op.f("pk_kernel_dependencies")),
    )
    op.create_index(
        op.f("ix_kernel_dependencies_depends_on"),
        "kernel_dependencies",
        ["depends_on"],
        unique=False,
    )
    op.create_index(
        op.f("ix_kernel_dependencies_kernel_id"), "kernel_dependencies", ["kernel_id"], unique=False
    )
    op.add_column(
        "kernels",
        sa.Column(
            "result",
            sa.Enum("UNDEFINED", "SUCCESS", "FAILURE", name="sessionresult"),
            default="UNDEFINED",
            server_default="UNDEFINED",
            nullable=False,
        ),
    )
    op.add_column("kernels", sa.Column("status_changed", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "kernels",
        sa.Column(
            "type",
            sa.Enum("INTERACTIVE", "BATCH", name="sessiontypes"),
            default="INTERACTIVE",
            server_default="INTERACTIVE",
            nullable=True,
        ),
    )
    op.alter_column("kernels", "agent_addr", existing_type=sa.VARCHAR(length=128), nullable=True)
    op.create_index(op.f("ix_kernels_result"), "kernels", ["result"], unique=False)
    op.create_index(op.f("ix_kernels_type"), "kernels", ["type"], unique=False)


def downgrade():
    conn = op.get_bind()
    conn.execute(text("ALTER TYPE kernelstatus RENAME TO kernelstatus_new;"))
    kernelstatus_old.create(conn)
    query = textwrap.dedent(
        """
        CREATE FUNCTION kernelstatus_new_old_compare(
            old_enum_val kernelstatus, new_enum_val kernelstatus_new
        )
            RETURNS boolean AS $$
                SELECT old_enum_val::text <> new_enum_val::text;
            $$ LANGUAGE SQL IMMUTABLE;
    """
    )
    conn.execute(text(query))
    queries = textwrap.dedent(
        """\
        CREATE OPERATOR <> (
            leftarg = kernelstatus,
            rightarg = kernelstatus_new,
            procedure = kernelstatus_new_old_compare
        );

        ALTER TABLE kernels
            ALTER COLUMN "status" DROP DEFAULT,
            ALTER COLUMN "status" TYPE kernelstatus USING (
                CASE "status"::text
                    WHEN 'PULLING' THEN 'PREPARING'
                    WHEN 'PENDING' THEN 'PREPARING'
                    ELSE "status"::text
                END
            )::kernelstatus,
            ALTER COLUMN "status" SET DEFAULT 'PREPARING'::kernelstatus;

        DROP FUNCTION kernelstatus_new_old_compare(
            old_enum_val kernelstatus, new_enum_val kernelstatus_new
        ) CASCADE;

        DROP TYPE kernelstatus_new;
    """
    )
    for query in queries.split(";"):
        if len(query.strip()) == 0:
            continue
        conn.execute(text(query))

    # op.drop_index(op.f("ix_kernels_type"), table_name="kernels")
    op.drop_index(op.f("ix_kernels_result"), table_name="kernels")
    op.alter_column("kernels", "agent_addr", existing_type=sa.VARCHAR(length=128), nullable=False)
    op.drop_column("kernels", "type")
    op.drop_column("kernels", "status_changed")
    op.drop_column("kernels", "result")
    op.drop_column("agents", "status_changed")
    op.drop_index(op.f("ix_kernel_dependencies_kernel_id"), table_name="kernel_dependencies")
    op.drop_index(op.f("ix_kernel_dependencies_depends_on"), table_name="kernel_dependencies")
    op.drop_table("kernel_dependencies")

    sessionresult.drop(op.get_bind())
    sessiontypes.drop(op.get_bind())
