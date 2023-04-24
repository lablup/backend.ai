"""add role column on kernels table

Revision ID: bedd92de93af
Revises: 3efd66393bd0
Create Date: 2023-04-24 11:57:53.111968

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from ai.backend.manager.models import ImageRow, KernelRole, kernels
from ai.backend.manager.models.base import EnumType

# revision identifiers, used by Alembic.
revision = "bedd92de93af"
down_revision = "3efd66393bd0"
branch_labels = None
depends_on = None

images = ImageRow.__table__
kernelrole_choices = list(map(lambda v: v.name, KernelRole))
kernelrole = postgresql.ENUM(*kernelrole_choices, name="kernelrole")


def upgrade():
    connection = op.get_bind()
    kernelrole.create(connection)
    op.add_column("kernels", sa.Column("role", EnumType(KernelRole), nullable=True))
    query = sa.select([kernels.c.id, kernels.c.image]).select_from(kernels)
    all_kernels = connection.execute(query).fetchall()
    for kernel in all_kernels:
        query = (
            sa.select([images.c.type]).select_from(images).where(images.c.name == kernel["image"])
        )
        image_type = connection.execute(query).scalar()
        if image_type is None:
            image_type = KernelRole.COMPUTE  # assume as Compute session
        query = sa.update(kernels).values({"role": image_type}).where(kernels.c.id == kernel["id"])
        connection.execute(query)
    op.alter_column("kernels", column_name="role", nullable=False)


def downgrade():
    op.drop_column("kernels", "role")
    kernelrole.drop(op.get_bind())
