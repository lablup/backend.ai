"""add domain model

Revision ID: bae1a7326e8a
Revises: 819c2b3830a9
Create Date: 2019-05-08 08:29:29.588817

"""

import textwrap

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import text

from ai.backend.manager.models.base import ResourceSlotColumn, convention

# revision identifiers, used by Alembic.
revision = "bae1a7326e8a"
down_revision = "819c2b3830a9"
branch_labels = None
depends_on = None


def upgrade():
    metadata = sa.MetaData(naming_convention=convention)

    # partial table to insert "default" domain
    domains = sa.Table(
        "domains",
        metadata,
        sa.Column("name", sa.String(length=64), primary_key=True),
        sa.Column("description", sa.String(length=512)),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("total_resource_slots", ResourceSlotColumn(), nullable=False),
    )

    op.create_table(
        "domains",
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("description", sa.String(length=512), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column(
            "modified_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("total_resource_slots", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("name", name=op.f("pk_domains")),
    )
    op.add_column("users", sa.Column("domain_name", sa.String(length=64), nullable=True))
    op.create_index(op.f("ix_users_domain_name"), "users", ["domain_name"], unique=False)
    op.create_foreign_key(
        op.f("fk_users_domain_name_domains"), "users", "domains", ["domain_name"], ["name"]
    )

    # Fill in users' domain_name column with default domain.
    # Create default domain if not exist.
    connection = op.get_bind()
    query = sa.select([domains]).select_from(domains).where(domains.c.name == "default")
    results = connection.execute(query).first()
    if results is None:
        query = sa.insert(domains).values(
            name="default", description="Default domain", is_active=True, total_resource_slots="{}"
        )
        query = textwrap.dedent(
            """\
            INSERT INTO domains (name, description, is_active, total_resource_slots)
            VALUES ('default', 'Default domain', True, '{}'::jsonb);"""
        )
        connection.execute(text(query))

    # Fill in users' domain_name field.
    query = "UPDATE users SET domain_name = 'default' WHERE email != 'admin@lablup.com';"
    connection.execute(text(query))


def downgrade():
    op.drop_constraint(op.f("fk_users_domain_name_domains"), "users", type_="foreignkey")
    op.drop_index(op.f("ix_users_domain_name"), table_name="users")
    op.drop_column("users", "domain_name")
    op.drop_table("domains")
