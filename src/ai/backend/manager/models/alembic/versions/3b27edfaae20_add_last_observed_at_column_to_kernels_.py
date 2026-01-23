"""Add last_observed_at column to kernels table

Revision ID: 3b27edfaae20
Revises: 352143f82276
Create Date: 2026-01-20 13:43:29.314925

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '3b27edfaae20'
down_revision = '352143f82276'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add last_observed_at column
    op.add_column(
        'kernels',
        sa.Column(
            'last_observed_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('NULL'),
            nullable=True,
        ),
    )

    # Partial index for running kernels (fair share observation)
    # Matches: terminated_at IS NULL AND starts_at IS NOT NULL
    op.create_index(
        'ix_kernels_fair_share_running',
        'kernels',
        ['scaling_group'],
        postgresql_where=sa.text('terminated_at IS NULL AND starts_at IS NOT NULL'),
    )

    # Partial index for terminated kernels (fair share observation)
    # Matches: terminated_at IS NOT NULL AND starts_at IS NOT NULL
    op.create_index(
        'ix_kernels_fair_share_terminated',
        'kernels',
        ['scaling_group', 'terminated_at'],
        postgresql_where=sa.text('terminated_at IS NOT NULL AND starts_at IS NOT NULL'),
    )


def downgrade() -> None:
    op.drop_index('ix_kernels_fair_share_terminated', table_name='kernels')
    op.drop_index('ix_kernels_fair_share_running', table_name='kernels')
    op.drop_column('kernels', 'last_observed_at')
