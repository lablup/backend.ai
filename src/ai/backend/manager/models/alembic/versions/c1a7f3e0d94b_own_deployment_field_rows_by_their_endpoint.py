"""own deployment field rows by their endpoint

Revision ID: c1a7f3e0d94b
Revises: b4c2e7f19a30
Create Date: 2026-09-07 16:10:00.000000

Access tokens and revisions are field rows of a deployment, so each must name exactly
one that exists. ``endpoint_tokens.endpoint`` had lost its foreign key and accepted
NULL, and ``deployment_revisions.endpoint`` carried no foreign key either; rows whose
endpoint is gone are unreachable and are deleted before the constraints go on.
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c1a7f3e0d94b"
down_revision = "b4c2e7f19a30"
branch_labels = None
depends_on = None

_TOKEN_FK = "fk_endpoint_tokens_endpoint_endpoints"
_REVISION_FK = "fk_deployment_revisions_endpoint_endpoints"


def _foreign_keys(table: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {fk["name"] for fk in inspector.get_foreign_keys(table) if fk["name"]}


def upgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM endpoint_tokens WHERE endpoint IS NULL"
            " OR endpoint NOT IN (SELECT id FROM endpoints)"
        )
    )
    op.alter_column(
        "endpoint_tokens", "endpoint", existing_type=sa.dialects.postgresql.UUID(), nullable=False
    )
    if _TOKEN_FK not in _foreign_keys("endpoint_tokens"):
        op.create_foreign_key(
            _TOKEN_FK,
            "endpoint_tokens",
            "endpoints",
            ["endpoint"],
            ["id"],
            ondelete="CASCADE",
        )

    op.execute(
        sa.text("DELETE FROM deployment_revisions WHERE endpoint NOT IN (SELECT id FROM endpoints)")
    )
    if _REVISION_FK not in _foreign_keys("deployment_revisions"):
        op.create_foreign_key(
            _REVISION_FK,
            "deployment_revisions",
            "endpoints",
            ["endpoint"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    if _REVISION_FK in _foreign_keys("deployment_revisions"):
        op.drop_constraint(_REVISION_FK, "deployment_revisions", type_="foreignkey")
    if _TOKEN_FK in _foreign_keys("endpoint_tokens"):
        op.drop_constraint(_TOKEN_FK, "endpoint_tokens", type_="foreignkey")
    op.alter_column(
        "endpoint_tokens", "endpoint", existing_type=sa.dialects.postgresql.UUID(), nullable=True
    )
