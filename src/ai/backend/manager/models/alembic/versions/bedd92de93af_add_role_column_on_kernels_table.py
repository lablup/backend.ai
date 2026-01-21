"""add role column on kernels table

Revision ID: bedd92de93af
Revises: 3efd66393bd0, 10c58e701d87
Create Date: 2023-04-24 11:57:53.111968

"""

import enum
import uuid
from typing import Any
from typing import cast as t_cast

import sqlalchemy as sa
from alembic import op
from sqlalchemy import cast
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import registry
from sqlalchemy.sql.functions import coalesce

from ai.backend.manager.models.base import GUID, EnumType, convention

# revision identifiers, used by Alembic.
revision = "bedd92de93af"
down_revision = ("3efd66393bd0", "10c58e701d87")
branch_labels = None
depends_on = None

metadata = sa.MetaData(naming_convention=convention)
mapper_registry = registry(metadata=metadata)
Base: Any = mapper_registry.generate_base()


class KernelRole(enum.Enum):
    INFERENCE = "INFERENCE"
    COMPUTE = "COMPUTE"
    SYSTEM = "SYSTEM"


images = sa.Table(
    "images",
    metadata,
    sa.Column("name", sa.String, nullable=False, index=True),
    sa.Column("labels", sa.JSON, nullable=False),
)

kernelrole_choices = list(map(lambda v: v.name, KernelRole))
kernelrole = postgresql.ENUM(*kernelrole_choices, name="kernelrole")


def upgrade():
    connection = op.get_bind()
    kernelrole.create(connection)
    op.add_column("kernels", sa.Column("role", EnumType(KernelRole), nullable=True))

    kernels = sa.Table(
        "kernels",
        metadata,
        sa.Column("id", GUID(), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "role",
            EnumType(KernelRole),
            default=KernelRole.COMPUTE,
            server_default=KernelRole.COMPUTE.name,
            nullable=False,
        ),
        sa.Column("image", sa.String(length=512)),
    )

    batch_size = 1000
    total_rowcount = 0
    while True:
        # Fetch records whose `role` is null only. This removes the use of offset from the query.
        # `order_by` is not necessary, but helpful to display the currently processing kernels.
        query = (
            sa.select(kernels.c.id)
            .where(kernels.c.role.is_(sa.null()))
            .order_by(kernels.c.id)
            .limit(batch_size)
        )
        result = connection.scalars(query).all()
        kernel_ids_to_update = t_cast(list[uuid.UUID], result)

        if not kernel_ids_to_update:
            break
        query = (
            sa.update(kernels)
            .values({
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
            })
            .where(kernels.c.id.in_(kernel_ids_to_update))
        )
        result = connection.execute(query)
        total_rowcount += result.rowcount
        print(f"total processed count: {total_rowcount} (~{kernel_ids_to_update[-1]})")

        if result.rowcount < batch_size:
            break

    op.alter_column("kernels", column_name="role", nullable=False)


def downgrade():
    op.drop_column("kernels", "role")
    kernelrole.drop(op.get_bind())
