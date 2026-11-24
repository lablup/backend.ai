"""Add interpolation to default session options

Writes the default service argument interpolation delimiters into
`scaling_groups.default_session_options` of the resource groups that lack them.

Revision ID: 4ab2e2e50939
Revises: 6f6d61f67ca0
Create Date: 2026-11-19

"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "4ab2e2e50939"  # Part of: NEXT_RELEASE_VERSION
down_revision = "6f6d61f67ca0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        UPDATE scaling_groups
        SET default_session_options = default_session_options || jsonb_build_object(
            'interpolation',
            jsonb_build_object(
                'delimiters',
                jsonb_build_array(
                    jsonb_build_object('start', '${{', 'end', '}}'),
                    jsonb_build_object('start', '{', 'end', '}')
                )
            )
        )
        WHERE NOT (default_session_options ? 'interpolation')
    """)


def downgrade() -> None:
    op.execute("""
        UPDATE scaling_groups
        SET default_session_options = default_session_options - 'interpolation'
    """)
