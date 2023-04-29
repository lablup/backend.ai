"""add role column on kernels table

Revision ID: bedd92de93af
Revises: 10c58e701d87
Create Date: 2023-04-24 11:57:53.111968

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy import case, cast
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.functions import coalesce

from ai.backend.manager.models import ImageRow, ImageType, KernelRole, kernels
from ai.backend.manager.models.base import EnumType

# revision identifiers, used by Alembic.
revision = "bedd92de93af"
down_revision = "10c58e701d87"
branch_labels = None
depends_on = None

images = ImageRow.__table__
kernelrole_choices = list(map(lambda v: v.name, KernelRole))
kernelrole = postgresql.ENUM(*kernelrole_choices, name="kernelrole")


def upgrade():
    connection = op.get_bind()
    kernelrole.create(connection)
    op.add_column("kernels", sa.Column("role", EnumType(KernelRole), nullable=True))

    # As the `ImageType` and `KernelRole` enum types are incompatible, we need to explicitly map the
    # values from `ImageType` to those of `KernelRole`.
    # NOTE: Omitting `.value` raises an error. The reason is unclear, but appending `.value`
    # and explicitly casting the query resolves the issue.
    # - `Error: column "role" is of type kernelrole but expression is of type text.`
    image_type_to_kernelrole = case(
        [
            (images.c.type == ImageType.COMPUTE, KernelRole.COMPUTE.value),
            (images.c.type == ImageType.SYSTEM, KernelRole.SYSTEM.value),
            (images.c.type == ImageType.SERVICE, KernelRole.INFERENCE.value),
        ],
        else_=KernelRole.COMPUTE.value,  # default value
    )

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

        query = (
            sa.update(kernels)
            .values({
                "role": cast(  # Explicit casting as described in `image_type_to_kernelrole` case.
                    coalesce(
                        # `sa.func.min` is introduced since it is possible (not prevented) for two
                        # records have the same image name. Without `sa.func.min`, the records
                        # raises multiple values error.
                        sa.select([sa.func.min(image_type_to_kernelrole)])
                        .select_from(images)
                        .where(images.c.name == kernels.c.image)
                        .as_scalar(),
                        # Set the default role when there is no matching image.
                        # This may occur when one of the previously used image is deleted.
                        KernelRole.COMPUTE.value,
                    ),
                    EnumType(KernelRole)
                )
            })
            .where(kernels.c.id.in_(kernel_ids_to_update))
        )
        result = connection.execute(query)
        total_rowcount += result.rowcount
        print(f'total processed count: {total_rowcount} (~{kernel_ids_to_update[-1]})')

        if result.rowcount < batch_size:
            break

    op.alter_column("kernels", column_name="role", nullable=False)


def downgrade():
    op.drop_column("kernels", "role")
    kernelrole.drop(op.get_bind())
