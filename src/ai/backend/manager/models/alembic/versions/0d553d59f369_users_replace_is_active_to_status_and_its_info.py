"""replace_users_is_active_to_status_and_its_info

Revision ID: 0d553d59f369
Revises: 9cd61b1ae70d
Create Date: 2020-07-04 23:44:09.191729

"""
import textwrap

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0d553d59f369'
down_revision = '9cd61b1ae70d'
branch_labels = None
depends_on = None

userstatus_choices = (
    'active',
    'inactive',
    'deleted',
    'before-verification',
)
userstatus = postgresql.ENUM(
    *userstatus_choices,
    name='userstatus'
)

def upgrade():
    userstatus.create(op.get_bind())
    op.add_column(
        'users',
        sa.Column('status', sa.Enum(*userstatus_choices, name='userstatus'), nullable=True)
    )
    op.add_column('users', sa.Column('status_info', sa.Unicode(), nullable=True))

    # Set user's status field.
    conn = op.get_bind()
    query = textwrap.dedent(
        "UPDATE users SET status = 'active', status_info = 'migrated' WHERE is_active = 't';"
    )
    conn.execute(query)
    query = textwrap.dedent(
        "UPDATE users SET status = 'inactive', status_info = 'migrated' WHERE is_active <> 't';"
    )
    conn.execute(query)

    op.alter_column('users', column_name='status', nullable=False)
    op.drop_column('users', 'is_active')


def downgrade():
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=True))

    # Set user's is_active field.
    conn = op.get_bind()
    query = textwrap.dedent("UPDATE users SET is_active = 't' WHERE status = 'active';")
    conn.execute(query)
    query = textwrap.dedent("UPDATE users SET is_active = 'f' WHERE status <> 'active';")
    conn.execute(query)

    op.drop_column('users', 'status_info')
    op.drop_column('users', 'status')
    userstatus.drop(op.get_bind())
