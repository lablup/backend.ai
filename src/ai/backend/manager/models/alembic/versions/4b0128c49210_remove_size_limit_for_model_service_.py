"""remove size limit for model_service_token.token

Revision ID: 4b0128c49210
Revises: 02535458c0b3
Create Date: 2023-09-01 10:55:44.074487

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import IDColumn

# revision identifiers, used by Alembic.
revision = "4b0128c49210"
down_revision = "02535458c0b3"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("pk_endpoint_tokens", "endpoint_tokens")
    op.add_column("endpoint_tokens", IDColumn())
    op.alter_column("endpoint_tokens", "token", type_=sa.String())


def downgrade():
    op.drop_column("pk_endpoint_tokens", "endpoint_tokens")
    op.drop_column("endpoint_tokens", "id")
    op.alter_column("endpoint_tokens", "token", type_=sa.VARCHAR(1024))
    op.create_primary_key("pk_endpoint_tokens", "endpoint_tokens", ["token"])
