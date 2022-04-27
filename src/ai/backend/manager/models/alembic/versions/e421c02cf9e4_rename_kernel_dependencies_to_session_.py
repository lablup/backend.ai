"""rename_kernel_dependencies_to_session_dependencies

Revision ID: e421c02cf9e4
Revises: 548cc8aa49c8
Create Date: 2020-09-14 10:45:40.218548

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'e421c02cf9e4'
down_revision = '548cc8aa49c8'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('fk_kernel_dependencies_depends_on_kernels', 'kernel_dependencies')
    op.drop_constraint('fk_kernel_dependencies_kernel_id_kernels', 'kernel_dependencies')
    op.rename_table('kernel_dependencies', 'session_dependencies')
    op.alter_column('session_dependencies', 'kernel_id', new_column_name='session_id')
    op.execute('ALTER INDEX pk_kernel_dependencies '
               'RENAME TO pk_session_dependencies')
    op.execute('ALTER INDEX ix_kernel_dependencies_depends_on '
               'RENAME TO ix_session_dependencies_depends_on')
    op.execute('ALTER INDEX ix_kernel_dependencies_kernel_id '
               'RENAME TO ix_session_dependencies_session_id')
    # NOTE: we keep the fkey target as "kernels.id" instead of "kernels.session_id"
    #       because fkey target must be a unique index and in Backend.AI `kernels.session_id`
    #       is same to the main kernel's `kernels.id`.
    op.create_foreign_key(None, 'session_dependencies', 'kernels', ['session_id'], ['id'],
                          onupdate='CASCADE', ondelete='CASCADE')
    op.create_foreign_key(None, 'session_dependencies', 'kernels', ['depends_on'], ['id'],
                          onupdate='CASCADE', ondelete='CASCADE')


def downgrade():
    op.drop_constraint('fk_session_dependencies_depends_on_kernels', 'session_dependencies')
    op.drop_constraint('fk_session_dependencies_session_id_kernels', 'session_dependencies')
    op.rename_table('session_dependencies', 'kernel_dependencies')
    op.alter_column('kernel_dependencies', 'session_id', new_column_name='kernel_id')
    op.execute('ALTER INDEX pk_session_dependencies '
               'RENAME TO pk_kernel_dependencies')
    op.execute('ALTER INDEX ix_session_dependencies_depends_on '
               'RENAME TO ix_kernel_dependencies_depends_on')
    op.execute('ALTER INDEX ix_session_dependencies_session_id '
               'RENAME TO ix_kernel_dependencies_kernel_id')
    op.create_foreign_key(None, 'kernel_dependencies', 'kernels', ['kernel_id'], ['id'],
                          onupdate='CASCADE', ondelete='CASCADE')
    op.create_foreign_key(None, 'kernel_dependencies', 'kernels', ['depends_on'], ['id'],
                          onupdate='CASCADE', ondelete='CASCADE')
