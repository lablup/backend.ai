"""change_endpoint_to_nullable

Revision ID: 589c764a18f1
Revises: 3f47af213b05
Create Date: 2024-02-27 20:18:55.524946

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID, convention

# revision identifiers, used by Alembic.
revision = "589c764a18f1"
down_revision = "3f47af213b05"
branch_labels = None
depends_on = None


metadata = sa.MetaData(naming_convention=convention)


BATCH_SIZE = 100


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
        sa.Column("id", GUID, primary_key=True),
        sa.Column(
            "endpoint", GUID, sa.ForeignKey("endpoints.id", ondelete="SET NULL"), nullable=True
        ),
        extend_existing=True,
    )
    endpoints = sa.Table(
        "endpoints",
        metadata,
        sa.Column("id", GUID, primary_key=True),
        sa.Column("model", GUID, sa.ForeignKey("vfolders.id", ondelete="SET NULL"), nullable=True),
        extend_existing=True,
    )

    def _delete(table, null_field):
        while True:
            subq = sa.select([table.c.id]).where(null_field.is_(sa.null())).limit(BATCH_SIZE)
            delete_stmt = sa.delete(table).where(table.c.id.in_(subq))
            result = conn.execute(delete_stmt)
            if result.rowcount == 0:
                break

    _delete(endpoint_tokens, endpoint_tokens.c.endpoint)
    _delete(endpoints, endpoints.c.model)

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
