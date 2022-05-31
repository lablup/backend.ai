"""more_status

Revision ID: 0f3bc98edaa0
Revises: 7ea324d0535b
Create Date: 2017-08-11 13:12:55.236519

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0f3bc98edaa0'
down_revision = '7ea324d0535b'
branch_labels = None
depends_on = None

agentstatus = postgresql.ENUM(
    'ALIVE', 'LOST', 'RESTARTING', 'TERMINATED',
    name='agentstatus',
)

kernelstatus_choices = (
    'PREPARING', 'BUILDING', 'RUNNING',
    'RESTARTING', 'RESIZING', 'SUSPENDED',
    'TERMINATING', 'TERMINATED', 'ERROR',
)
kernelstatus = postgresql.ENUM(
    *kernelstatus_choices,
    name='kernelstatus')


def upgrade():
    agentstatus.create(op.get_bind())
    kernelstatus.create(op.get_bind())
    op.add_column('agents', sa.Column('lost_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('agents', sa.Column('status', sa.Enum('ALIVE', 'LOST', 'RESTARTING', 'TERMINATED', name='agentstatus'), nullable=False))
    op.create_index(op.f('ix_agents_status'), 'agents', ['status'], unique=False)
    op.add_column('kernels', sa.Column('agent_addr', sa.String(length=128), nullable=False))
    op.add_column('kernels', sa.Column('cpu_slot', sa.Integer(), nullable=False))
    op.add_column('kernels', sa.Column('gpu_slot', sa.Integer(), nullable=False))
    op.add_column('kernels', sa.Column('mem_slot', sa.Integer(), nullable=False))
    op.add_column('kernels', sa.Column('repl_in_port', sa.Integer(), nullable=False))
    op.add_column('kernels', sa.Column('repl_out_port', sa.Integer(), nullable=False))
    op.add_column('kernels', sa.Column('stdin_port', sa.Integer(), nullable=False))
    op.add_column('kernels', sa.Column('stdout_port', sa.Integer(), nullable=False))
    op.drop_column('kernels', 'allocated_cores')
    op.add_column('kernels', sa.Column('cpu_set', sa.ARRAY(sa.Integer), nullable=True))
    op.add_column('kernels', sa.Column('gpu_set', sa.ARRAY(sa.Integer), nullable=True))
    op.alter_column('kernels', column_name='status', type_=sa.Enum(*kernelstatus_choices, name='kernelstatus'),
                    postgresql_using='status::kernelstatus')


def downgrade():
    op.drop_column('kernels', 'stdout_port')
    op.drop_column('kernels', 'stdin_port')
    op.drop_column('kernels', 'repl_out_port')
    op.drop_column('kernels', 'repl_in_port')
    op.drop_column('kernels', 'mem_slot')
    op.drop_column('kernels', 'gpu_slot')
    op.drop_column('kernels', 'cpu_slot')
    op.drop_column('kernels', 'agent_addr')
    op.drop_index(op.f('ix_agents_status'), table_name='agents')
    op.drop_column('agents', 'status')
    op.drop_column('agents', 'lost_at')
    op.alter_column('kernels', column_name='status', type_=sa.String(length=64))
    op.add_column('kernels', sa.Column('allocated_cores', sa.ARRAY(sa.Integer), nullable=True))
    op.drop_column('kernels', 'cpu_set')
    op.drop_column('kernels', 'gpu_set')
    agentstatus.drop(op.get_bind())
    kernelstatus.drop(op.get_bind())
