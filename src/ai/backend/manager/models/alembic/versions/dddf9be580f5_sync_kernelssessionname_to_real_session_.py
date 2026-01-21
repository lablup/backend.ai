"""sync_kernelssessionname_to_real_session_name

Revision ID: dddf9be580f5
Revises: 857b763b8618
Create Date: 2024-04-01 16:58:14.341114

"""

import textwrap

from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = "dddf9be580f5"
down_revision = "857b763b8618"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    sync_stmt = textwrap.dedent(
        """
        UPDATE kernels
        SET session_name = sessions.name
        FROM sessions
        WHERE kernels.session_id = sessions.id
        AND kernels.session_name <> sessions.name;
        """
    )
    conn.execute(text(sync_stmt))


def downgrade():
    pass
