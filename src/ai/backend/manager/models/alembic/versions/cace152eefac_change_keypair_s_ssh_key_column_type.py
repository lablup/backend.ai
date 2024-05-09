"""change keypair's ssh key column type

Revision ID: cace152eefac
Revises: 213a04e90ecf
Create Date: 2023-02-10 15:43:51.482204

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "cace152eefac"
down_revision = "213a04e90ecf"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "keypairs", "ssh_public_key", existing_type=sa.String(length=750), type_=sa.Text
    )
    op.alter_column(
        "keypairs", "ssh_private_key", existing_type=sa.String(length=2000), type_=sa.Text
    )


def downgrade():
    print("existing keys will be truncated to 750 (public)/2000 (private) bytes")
    op.alter_column(
        "keypairs", "ssh_public_key", existing_type=sa.Text, type_=sa.String(length=750)
    )
    op.alter_column(
        "keypairs", "ssh_private_key", existing_type=sa.Text, type_=sa.String(length=2000)
    )
