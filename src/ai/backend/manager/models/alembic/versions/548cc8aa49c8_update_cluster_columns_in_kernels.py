"""update_cluster_columns_in_kernels

Revision ID: 548cc8aa49c8
Revises: 1e673659b283
Create Date: 2020-09-08 18:50:05.594899

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '548cc8aa49c8'
down_revision = '1e673659b283'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index('ix_kernels_sess_id_role', table_name='kernels')
    op.drop_index('ix_kernels_unique_sess_token', table_name='kernels')

    op.add_column('kernels', sa.Column('cluster_size', sa.Integer, nullable=False,
                                       default=1, server_default=sa.text('1')))
    op.add_column('kernels', sa.Column('cluster_hostname', sa.String(length=64), nullable=True))
    conn = op.get_bind()
    query = "UPDATE kernels k " \
            "  SET cluster_size = (SELECT COUNT(*) FROM kernels j WHERE j.session_id = k.session_id);"
    conn.execute(query)
    query = "UPDATE kernels SET cluster_hostname = CONCAT(role, CAST(idx AS TEXT));"
    conn.execute(query)
    op.alter_column('kernels', 'cluster_hostname', nullable=False)

    op.alter_column('kernels', 'idx', new_column_name='cluster_idx', nullable=False)
    op.alter_column('kernels', 'role', new_column_name='cluster_role', nullable=False)

    op.create_index('ix_kernels_sess_id_role', 'kernels', ['session_id', 'cluster_role'], unique=False)
    op.create_index('ix_kernels_unique_sess_token', 'kernels', ['access_key', 'session_id'], unique=True,
                    postgresql_where=sa.text("status NOT IN ('TERMINATED', 'CANCELLED') "
                                             "and cluster_role = 'main'"))


def downgrade():
    op.drop_index('ix_kernels_unique_sess_token', table_name='kernels')
    op.drop_index('ix_kernels_sess_id_role', table_name='kernels')

    op.alter_column('kernels', 'cluster_idx', new_column_name='idx')
    op.alter_column('kernels', 'cluster_role', new_column_name='role')
    op.drop_column('kernels', 'cluster_size')
    op.drop_column('kernels', 'cluster_hostname')

    op.create_index('ix_kernels_unique_sess_token', 'kernels',
                    ['access_key', 'session_name'], unique=True,
                    postgresql_where=sa.text("status NOT IN ('TERMINATED', 'CANCELLED') "
                                             "and role = 'main'"))
    op.create_index('ix_kernels_sess_id_role', 'kernels', ['session_name', 'role'], unique=False)
