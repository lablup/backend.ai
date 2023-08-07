"""remove kernels.role

Revision ID: ead95145e6f0
Revises: eb9441fcf90a
Create Date: 2023-08-07 14:48:01.346306

"""
import enum

import sqlalchemy as sa
from alembic import op
from sqlalchemy import cast
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.functions import coalesce

from ai.backend.manager.models.base import EnumType, IDColumn, SessionIDColumnType, convention

# revision identifiers, used by Alembic.
revision = "ead95145e6f0"
down_revision = "eb9441fcf90a"
branch_labels = None
depends_on = None


class KernelRole(enum.Enum):
    INFERENCE = "INFERENCE"
    COMPUTE = "COMPUTE"
    SYSTEM = "SYSTEM"


kernelrole_choices = list(map(lambda v: v.name, KernelRole))
kernelrole = postgresql.ENUM(*kernelrole_choices, name="kernelrole")

metadata = sa.MetaData(naming_convention=convention)

sessions = sa.Table(
    "sessions",
    metadata,
    IDColumn(),
    sa.Column("is_system_session", sa.Boolean(), default=False, nullable=False),
)

kernels = sa.Table(
    "kernels",
    metadata,
    IDColumn(),
    sa.Column(
        "session_id",
        SessionIDColumnType,
        sa.ForeignKey("sessions.id"),
        unique=False,
        index=True,
        nullable=False,
    ),
    sa.Column(
        "role",
        EnumType(KernelRole),
        default=KernelRole.COMPUTE,
        server_default=KernelRole.COMPUTE.name,
        nullable=False,
        index=True,
    ),
    sa.Column("image", sa.String(length=512)),
    sa.Column("is_system_kernel", sa.Boolean(), default=False, nullable=False),
)

images = sa.Table(
    "images",
    metadata,
    sa.Column("name", sa.String, nullable=False, index=True),
    sa.Column("labels", sa.JSON, nullable=False),
)


def upgrade():
    op.add_column(
        "sessions",
        sa.Column(
            "is_system_session", sa.Boolean(), default=False, server_default="0", nullable=False
        ),
    )
    op.add_column(
        "kernels",
        sa.Column(
            "is_system_kernel", sa.Boolean(), default=False, server_default="0", nullable=False
        ),
    )

    conn = op.get_bind()
    query = (
        kernels.update()
        .values({"is_system_kernel": True})
        .where(kernels.c.role == KernelRole.SYSTEM)
    )
    conn.execute(query)

    query = (
        sessions.update()
        .values({"is_system_session": True})
        .where((sessions.c.id == kernels.c.session_id) & (kernels.c.is_system_kernel == True))
    )
    conn.execute(query)

    op.drop_column("kernels", "role")


def downgrade():
    connection = op.get_bind()
    kernelrole.create(connection)
    op.add_column("kernels", sa.Column("role", EnumType(KernelRole), nullable=True))

    batch_size = 1000
    total_rowcount = 0
    while True:
        # Fetch records whose `role` is null only. This removes the use of offset from the query.
        # `order_by` is not necessary, but helpful to display the currently processing kernels.
        query = (
            sa.select([kernels.c.id])
            .where(kernels.c.role == None)
            .order_by(kernels.c.id)
            .limit(batch_size)
        )
        result = connection.execute(query).fetchall()
        kernel_ids_to_update = [kid[0] for kid in result]

        if not kernel_ids_to_update:
            break
        query = (
            sa.update(kernels)
            .values(
                {
                    "role": cast(
                        coalesce(
                            # `limit(1)` is introduced since it is possible (not prevented) for two
                            # records have the same image name. Without `limit(1)`, the records
                            # raises multiple values error.
                            sa.select([images.c.labels.op("->>")("ai.backend.role")])
                            .select_from(images)
                            .where(images.c.name == kernels.c.image)
                            .limit(1)
                            .as_scalar(),
                            # Set the default role when there is no matching image.
                            # This may occur when one of the previously used image is deleted.
                            KernelRole.COMPUTE.value,
                        ),
                        EnumType(KernelRole),
                    )
                }
            )
            .where(kernels.c.id.in_(kernel_ids_to_update))
        )
        result = connection.execute(query)
        total_rowcount += result.rowcount
        print(f"total processed count: {total_rowcount} (~{kernel_ids_to_update[-1]})")

        if result.rowcount < batch_size:
            break

    op.alter_column("kernels", column_name="role", nullable=False)

    op.drop_column("sessions", "is_system_session")
    op.drop_column("kernels", "is_system_kernel")
