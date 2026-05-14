"""add ``id`` UUID column to ``domains`` and demote ``name`` to unique

Adds a UUID ``id`` column as the new primary key of the ``domains`` table.
The legacy ``name`` column becomes a UNIQUE column so that existing foreign
key references continue to function.

Because PostgreSQL tracks foreign-key dependencies on the primary-key index
itself (not the underlying column), the swap requires temporarily dropping
and recreating every FK that points to ``domains.name``. The FK definitions
are restored with identical semantics (column, target column, and
ON UPDATE/DELETE rules unchanged).

Revision ID: a1c3e5d7b9f2
Revises: b2c3d4e5f6a7
Create Date: 2026-05-15

"""

# Part of: 26.5.0

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "a1c3e5d7b9f2"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


# (referencing_table, fk_constraint_name, fk_column, on_update, on_delete)
_DOMAIN_FK_REFS: tuple[tuple[str, str, str, str | None, str | None], ...] = (
    ("endpoint_tokens", "fk_endpoint_tokens_domain_domains", "domain", None, "CASCADE"),
    ("endpoints", "fk_endpoints_domain_domains", "domain", None, "RESTRICT"),
    ("groups", "fk_groups_domain_name_domains", "domain_name", "CASCADE", "CASCADE"),
    ("kernels", "fk_kernels_domain_name_domains", "domain_name", None, None),
    ("model_cards", "fk_model_cards_domain_domains", "domain", None, "RESTRICT"),
    ("routings", "fk_routings_domain_domains", "domain", None, "RESTRICT"),
    ("session_templates", "fk_session_templates_domain_name_domains", "domain_name", None, None),
    ("sessions", "fk_sessions_domain_name_domains", "domain_name", None, None),
    (
        "sgroups_for_domains",
        "fk_sgroups_for_domains_domain_domains",
        "domain",
        "CASCADE",
        "CASCADE",
    ),
    ("users", "fk_users_domain_name_domains", "domain_name", None, None),
)


def upgrade() -> None:
    op.add_column(
        "domains",
        sa.Column(
            "id",
            GUID(),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
    )

    for table, fk_name, _column, _on_update, _on_delete in _DOMAIN_FK_REFS:
        op.drop_constraint(fk_name, table, type_="foreignkey")

    op.create_unique_constraint("uq_domains_name", "domains", ["name"])
    op.drop_constraint("pk_domains", "domains", type_="primary")
    op.create_primary_key("pk_domains", "domains", ["id"])

    for table, fk_name, column, on_update, on_delete in _DOMAIN_FK_REFS:
        op.create_foreign_key(
            fk_name,
            table,
            "domains",
            [column],
            ["name"],
            onupdate=on_update,
            ondelete=on_delete,
        )


def downgrade() -> None:
    for table, fk_name, _column, _on_update, _on_delete in _DOMAIN_FK_REFS:
        op.drop_constraint(fk_name, table, type_="foreignkey")

    op.drop_constraint("pk_domains", "domains", type_="primary")
    op.drop_constraint("uq_domains_name", "domains", type_="unique")
    op.create_primary_key("pk_domains", "domains", ["name"])
    op.drop_column("domains", "id")

    for table, fk_name, column, on_update, on_delete in _DOMAIN_FK_REFS:
        op.create_foreign_key(
            fk_name,
            table,
            "domains",
            [column],
            ["name"],
            onupdate=on_update,
            ondelete=on_delete,
        )
