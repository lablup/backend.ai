"""add association `ContainerRegistries` with `Users` table.

Revision ID: c0b46faaa9fe
Revises: 1d42c726d8a3
Create Date: 2024-03-16 19:39:02.043247
"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID, Base, IDColumn, StrEnumType
from ai.backend.manager.models.container_registry import ContainerRegistryType

# revision identifiers, used by Alembic.
revision = "c0b46faaa9fe"
down_revision = "1d42c726d8a3"
branch_labels = None
depends_on = None


class AssociationContainerRegistriesUsers(Base):
    __tablename__ = "association_container_registries_users"
    __table_args__ = {"extend_existing": True}
    id = IDColumn()
    container_registry_id = sa.Column(
        "container_registry_id",
        GUID,
        sa.ForeignKey("container_registries.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = sa.Column(
        "user_id",
        GUID,
        sa.ForeignKey("users.uuid", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )


def get_container_registry_row_schema():
    class ContainerRegistryRow(Base):
        __tablename__ = "container_registries"
        __table_args__ = {"extend_existing": True}
        id = IDColumn()
        url = sa.Column("url", sa.String(length=512), index=True)
        registry_name = sa.Column("registry_name", sa.String(length=50), index=True)
        type = sa.Column(
            "type",
            StrEnumType(ContainerRegistryType),
            default=ContainerRegistryType.DOCKER,
            server_default=ContainerRegistryType.DOCKER,
            nullable=False,
            index=True,
        )
        project = sa.Column("project", sa.String(length=255), nullable=True)  # harbor only
        username = sa.Column("username", sa.String(length=255), nullable=True)
        password = sa.Column("password", sa.String(length=255), nullable=True)
        ssl_verify = sa.Column("ssl_verify", sa.Boolean, server_default=sa.text("true"), index=True)
        is_global = sa.Column("is_global", sa.Boolean, server_default=sa.text("true"), index=True)

    return ContainerRegistryRow


def upgrade():
    op.create_table(
        "association_container_registries_users",
        IDColumn("id"),
        sa.Column(
            "container_registry_id",
            GUID,
            sa.ForeignKey("container_registries.id", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            GUID,
            sa.ForeignKey("users.uuid", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False,
        ),
    )

    ContainerRegistries = get_container_registry_row_schema()

    db_conn = op.get_bind()
    container_registry_ids = db_conn.execute(sa.select(ContainerRegistries.id)).scalars().all()
    user_ids = (
        db_conn.execute(sa.select(sa.text("uuid")).select_from(sa.text("users"))).scalars().all()
    )

    query = sa.insert(AssociationContainerRegistriesUsers).values(
        container_registry_id=sa.bindparam("container_registry_id"),
        user_id=sa.bindparam("user_id"),
    )

    for container_registry_id in container_registry_ids:
        for user_id in user_ids:
            db_conn.execute(
                query,
                [{"container_registry_id": container_registry_id, "user_id": user_id}],
            )


def downgrade():
    op.drop_table("association_container_registries_users")
