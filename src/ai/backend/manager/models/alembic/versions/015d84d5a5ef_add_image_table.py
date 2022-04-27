"""add image table

Revision ID: 015d84d5a5ef
Revises: 60a1effa77d2
Create Date: 2022-02-15 23:45:19.814677

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from ai.backend.manager.models.base import ForeignKeyIDColumn, IDColumn, convention

from ai.backend.manager.models.image import ImageType


# revision identifiers, used by Alembic.
revision = '015d84d5a5ef'
down_revision = '60a1effa77d2'
branch_labels = None
depends_on = None


def upgrade():
    metadata = sa.MetaData(naming_convention=convention)
    op.create_table(
        'images', metadata,
        IDColumn('id'),
        sa.Column('name', sa.String, index=True, nullable=False),
        sa.Column('image', sa.String, nullable=False, index=True),
        sa.Column(
            'created_at', sa.DateTime(timezone=True),
            server_default=sa.func.now(), index=True),
        sa.Column('tag', sa.String, nullable=False, index=True),
        sa.Column('registry', sa.String, nullable=False, index=True),
        sa.Column('architecture', sa.String, nullable=False, server_default='x86_64', index=True),
        sa.Column('config_digest', sa.CHAR(length=72), nullable=False),
        sa.Column('size_bytes', sa.BigInteger, nullable=False),
        sa.Column('type', sa.Enum(ImageType, name='image_type'), nullable=False),
        sa.Column('accelerators', sa.String),
        sa.Column('labels', postgresql.JSONB(), nullable=False),
        sa.Column('resources', postgresql.JSONB(), nullable=False),
        sa.Index('ix_image_name_architecture', 'name', 'architecture', unique=True),
        sa.Index('ix_image_image_tag_registry', 'image', 'tag', 'registry'),
    )

    op.create_table(
        'image_aliases', metadata,
        IDColumn('id'),
        sa.Column('alias', sa.String, unique=True, index=True),
        ForeignKeyIDColumn('image', 'images.id', nullable=False),
        sa.Index('ix_image_alias_unique_ref', 'image', 'alias', unique=True),
    )


def downgrade():
    op.drop_table('image_aliases')
    op.drop_table('images')
    op.execute('DROP TYPE image_type')
