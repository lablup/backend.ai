"""Create task_template table

Revision ID: ce209920f654
Revises: 5e88398bc340
Create Date: 2019-12-16 13:39:13.210996

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from ai.backend.manager.models.base import GUID, IDColumn, ForeignKeyIDColumn


# revision identifiers, used by Alembic.
revision = 'ce209920f654'
down_revision = '65c4a109bbc7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'session_templates',
        IDColumn('id'),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), index=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('type',
                  sa.Enum('TASK', 'CLUSTER', name='templatetypes'),
                  nullable=False,
                  server_default='TASK'
                  ),
        sa.Column('domain_name', sa.String(length=64), sa.ForeignKey('domains.name'), nullable=False),
        sa.Column('group_id', GUID, sa.ForeignKey('groups.id'), nullable=True),
        sa.Column('user_uuid', GUID, sa.ForeignKey('users.uuid'), nullable=False),

        sa.Column('name', sa.String(length=128), nullable=True),
        sa.Column('template', sa.String(length=16 * 1024), nullable=False)
    )
    op.add_column(
        'kernels',
        sa.Column('bootstrap_script', sa.String(length=4 * 1024), nullable=True)
    )


def downgrade():
    op.drop_table('session_templates')
    op.execute('DROP TYPE templatetypes')
    op.drop_column('kernels', 'bootstrap_script')
