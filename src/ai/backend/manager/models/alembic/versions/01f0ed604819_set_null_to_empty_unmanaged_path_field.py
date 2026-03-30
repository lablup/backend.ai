"""set null to empty unmanaged_path field

Revision ID: 01f0ed604819
Revises: 17ea44123131
Create Date: 2025-07-02 16:31:50.692652

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "01f0ed604819"
down_revision = "17ea44123131"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    UPDATE vfolders
    SET unmanaged_path = NULL
    WHERE unmanaged_path = '';
    """)


def downgrade() -> None:
    # Downgrade is not implemented as the operation is irreversible.
    pass
