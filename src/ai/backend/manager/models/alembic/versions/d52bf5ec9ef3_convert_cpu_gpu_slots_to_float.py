"""convert_cpu_gpu_slots_to_float

Revision ID: d52bf5ec9ef3
Revises: 4545f5c948b3
Create Date: 2017-11-09 14:30:20.737908

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d52bf5ec9ef3"
down_revision = "4545f5c948b3"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("agents", "mem_slots", existing_type=sa.Integer(), type_=sa.BigInteger())
    op.alter_column("agents", "cpu_slots", existing_type=sa.Integer(), type_=sa.Float())
    op.alter_column("agents", "gpu_slots", existing_type=sa.Integer(), type_=sa.Float())
    op.alter_column("agents", "used_mem_slots", existing_type=sa.Integer(), type_=sa.BigInteger())
    op.alter_column("agents", "used_cpu_slots", existing_type=sa.Integer(), type_=sa.Float())
    op.alter_column("agents", "used_gpu_slots", existing_type=sa.Integer(), type_=sa.Float())
    op.alter_column("kernels", "mem_slot", existing_type=sa.Integer(), type_=sa.BigInteger())
    op.alter_column("kernels", "cpu_slot", existing_type=sa.Integer(), type_=sa.Float())
    op.alter_column("kernels", "gpu_slot", existing_type=sa.Integer(), type_=sa.Float())


def downgrade():
    op.alter_column("agents", "mem_slots", existing_type=sa.BigInteger(), type_=sa.Integer())
    op.alter_column("agents", "cpu_slots", existing_type=sa.Float(), type_=sa.Integer())
    op.alter_column("agents", "gpu_slots", existing_type=sa.Float(), type_=sa.Integer())
    op.alter_column("agents", "used_mem_slots", existing_type=sa.BigInteger(), type_=sa.Integer())
    op.alter_column("agents", "used_cpu_slots", existing_type=sa.Float(), type_=sa.Integer())
    op.alter_column("agents", "used_gpu_slots", existing_type=sa.Float(), type_=sa.Integer())
    op.alter_column("kernels", "mem_slot", existing_type=sa.BigInteger(), type_=sa.Integer())
    op.alter_column("kernels", "cpu_slot", existing_type=sa.Float(), type_=sa.Integer())
    op.alter_column("kernels", "gpu_slot", existing_type=sa.Float(), type_=sa.Integer())
