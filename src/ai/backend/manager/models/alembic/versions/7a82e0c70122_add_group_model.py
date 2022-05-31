"""add group model

Revision ID: 7a82e0c70122
Revises: bae1a7326e8a
Create Date: 2019-05-09 10:00:55.788734

"""
from alembic import op
import sqlalchemy as sa
from ai.backend.manager.models.base import GUID


# revision identifiers, used by Alembic.
revision = '7a82e0c70122'
down_revision = 'bae1a7326e8a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'groups',
        sa.Column('id', GUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('description', sa.String(length=512), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('modified_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('domain_name', sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(['domain_name'], ['domains.name'],
                                name=op.f('fk_groups_domain_name_domains'),
                                onupdate='CASCADE', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_groups')),
        sa.UniqueConstraint('name', 'domain_name', name='uq_groups_name_domain_name')
    )
    op.create_index(op.f('ix_groups_domain_name'), 'groups', ['domain_name'], unique=False)
    op.create_table(
        'association_groups_users',
        sa.Column('user_id',  GUID(), nullable=False),
        sa.Column('group_id', GUID(), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'],
                                name=op.f('fk_association_groups_users_group_id_groups'),
                                onupdate='CASCADE', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.uuid'],
                                name=op.f('fk_association_groups_users_user_id_users'),
                                onupdate='CASCADE', ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'group_id', name='uq_association_user_id_group_id')
    )


def downgrade():
    op.drop_table('association_groups_users')
    op.drop_index(op.f('ix_groups_domain_name'), table_name='groups')
    op.drop_table('groups')
