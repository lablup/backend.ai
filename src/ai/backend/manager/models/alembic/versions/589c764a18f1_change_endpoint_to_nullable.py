"""change_endpoint_to_nullable

Revision ID: 589c764a18f1
Revises: 7ff52ff68bfc
Create Date: 2024-02-27 20:18:55.524946

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID, convention

# revision identifiers, used by Alembic.
revision = "589c764a18f1"
down_revision = "7ff52ff68bfc"
branch_labels = None
depends_on = None


metadata = sa.MetaData(naming_convention=convention)


def upgrade():
    op.alter_column("endpoints", "model", nullable=True)
    op.drop_constraint(
        "fk_endpoint_tokens_endpoint_endpoints", "endpoint_tokens", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk_endpoint_tokens_endpoint_endpoints"),
        "endpoint_tokens",
        "endpoints",
        ["endpoint"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_constraint("fk_endpoints_model_vfolders", "endpoints", type_="foreignkey")
    op.create_foreign_key(
        op.f("fk_endpoints_model_vfolders"),
        "endpoints",
        "vfolders",
        ["model"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    conn = op.get_bind()

    endpoint_tokens = sa.Table(
        "endpoint_tokens",
        metadata,
        sa.Column(
            "endpoint", GUID, sa.ForeignKey("endpoints.id", ondelete="SET NULL"), nullable=True
        ),
        extend_existing=True,
    )
    endpoints = sa.Table(
        "endpoints",
        sa.Column("model", GUID, sa.ForeignKey("vfolders.id", ondelete="SET NULL"), nullable=True),
        extend_existing=True,
    )
    delete_endpoint_tokens = sa.delete(endpoint_tokens).where(
        endpoint_tokens.c.endpoint.is_(sa.null())
    )
    conn.execute(delete_endpoint_tokens)

    delete_endpoints = sa.delete(endpoints).where(endpoints.c.model.is_(sa.null()))
    conn.execute(delete_endpoints)

    op.drop_constraint(op.f("fk_endpoints_model_vfolders"), "endpoints", type_="foreignkey")
    op.create_foreign_key(
        "fk_endpoints_model_vfolders",
        "endpoints",
        "vfolders",
        ["model"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.alter_column("endpoints", "model", nullable=False)
    op.drop_constraint(
        op.f("fk_endpoint_tokens_endpoint_endpoints"), "endpoint_tokens", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_endpoint_tokens_endpoint_endpoints",
        "endpoint_tokens",
        "endpoints",
        ["endpoint"],
        ["id"],
    )
