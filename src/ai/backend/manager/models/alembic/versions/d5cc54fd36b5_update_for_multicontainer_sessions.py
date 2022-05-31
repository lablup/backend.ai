"""Update for multi-container sessions.

Revision ID: d5cc54fd36b5
Revises: 0d553d59f369
Create Date: 2020-01-06 13:56:50.885635

"""
from alembic import op
import sqlalchemy as sa

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = 'd5cc54fd36b5'
down_revision = '0d553d59f369'
branch_labels = None
depends_on = None


def upgrade():
    # In this mgiration, we finally clear up the column namings:
    #   sess_id -> session_name
    #     => client-provided alias
    #   (new) -> session_id
    #     => for single-container sessions, it may be derived from the kernel id.
    #   sess_type -> session_type
    #
    op.drop_index('ix_kernels_sess_id', table_name='kernels')
    op.drop_index('ix_kernels_sess_type', table_name='kernels')

    conn = op.get_bind()
    op.add_column(
        'kernels',
        sa.Column('idx', sa.Integer, nullable=True, default=None))
    op.add_column(
        'kernels',
        sa.Column('cluster_mode', sa.String(16), nullable=False,
                  default='single-node', server_default='single-node'))

    # Set idx to 1 (previous sessions are all composed of one kernel)
    query = "UPDATE kernels SET idx = 1;"
    conn.execute(query)

    # Convert "master" to "main"
    # NOTE: "main" is defined from ai.backend.manager.defs.DEFAULT_ROLE
    op.alter_column('kernels', 'role', server_default='main')
    query = "UPDATE kernels SET role = 'main' WHERE role = 'master'"
    conn.execute(query)

    # First a session_id column as nullable and fill it up before setting it non-nullable.
    op.add_column('kernels', sa.Column('session_id', GUID, nullable=True))
    query = "UPDATE kernels SET session_id = kernels.id WHERE role = 'main'"
    conn.execute(query)
    # If we upgrade from a database downgraded in the past with sub-kernel records,
    # we loose the information of kernel_id -> session_id mapping.
    # Try to restore it by getting the session ID of a main-kernel record which is created
    # at a similar time range.  This will raise an error if there are two or more such records,
    # and it is based on an assumption that development setups with manual tests would not make such
    # overlaps.
    query = """
    UPDATE kernels t SET session_id = (
        SELECT session_id
        FROM kernels s
        WHERE
            s.role = 'main'
            AND (
                s.created_at BETWEEN
                t.created_at - (interval '0.5s')
                AND t.created_at + (interval '3s')
            )
    )
    WHERE t.role <> 'main'
    """
    conn.execute(query)
    op.alter_column('kernels', 'session_id', nullable=False)

    op.alter_column('kernels', 'sess_id', new_column_name='session_name')
    op.alter_column('kernels', 'sess_type', new_column_name='session_type')

    op.create_index(op.f('ix_kernels_session_id'), 'kernels', ['session_id'], unique=False)
    op.create_index(op.f('ix_kernels_session_name'), 'kernels', ['session_name'], unique=False)
    op.create_index(op.f('ix_kernels_session_type'), 'kernels', ['session_type'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_kernels_session_type'), table_name='kernels')
    op.drop_index(op.f('ix_kernels_session_name'), table_name='kernels')
    op.drop_index(op.f('ix_kernels_session_id'), table_name='kernels')

    op.alter_column('kernels', 'session_type', new_column_name='sess_type')
    op.alter_column('kernels', 'session_name', new_column_name='sess_id')
    op.drop_column('kernels', 'session_id')

    # Convert "main" to "master" for backward compatibility
    op.alter_column('kernels', 'role', server_default='master')
    conn = op.get_bind()
    query = "UPDATE kernels SET role = 'master' WHERE role = 'main'"
    conn.execute(query)

    op.drop_column('kernels', 'cluster_mode')
    op.drop_column('kernels', 'idx')

    op.create_index('ix_kernels_sess_type', 'kernels', ['sess_type'], unique=False)
    op.create_index('ix_kernels_sess_id', 'kernels', ['sess_id'], unique=False)
