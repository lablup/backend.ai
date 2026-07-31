"""Add name_template to role_presets

A role preset may carry a Jinja template (e.g. ``{{scope.type}}-{{scope.name}}-member``)
rendering the name of roles instantiated from it; NULL keeps the preset's
fixed name.

Create Date: 2026-07-31

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b17bba59db34"
down_revision = "9fbeda8995ff"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "role_presets",
        sa.Column("name_template", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("role_presets", "name_template")
