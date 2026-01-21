"""Add project column to image table

Revision ID: 7c8501cec07b
Revises: 1d42c726d8a3
Create Date: 2024-08-10 07:29:39.492116

"""

import enum

import sqlalchemy as sa
import trafaret as t
from alembic import op

from ai.backend.manager.models.base import GUID, Base, IDColumn, StrEnumType, StructuredJSONColumn

# revision identifiers, used by Alembic.
revision = "7c8501cec07b"
down_revision = "1d42c726d8a3"
branch_labels = None
depends_on = None


def get_container_registry_row_schema():
    class ContainerRegistryType(enum.StrEnum):
        DOCKER = "docker"
        HARBOR = "harbor"
        HARBOR2 = "harbor2"
        LOCAL = "local"

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
        project = sa.Column("project", sa.String(length=255), nullable=True)
        username = sa.Column("username", sa.String(length=255), nullable=True)
        password = sa.Column("password", sa.String, nullable=True)
        ssl_verify = sa.Column("ssl_verify", sa.Boolean, server_default=sa.text("true"), index=True)
        is_global = sa.Column("is_global", sa.Boolean, server_default=sa.text("true"), index=True)

    return ContainerRegistryRow


def get_image_row_schema():
    class ImageType(enum.Enum):
        COMPUTE = "compute"
        SYSTEM = "system"
        SERVICE = "service"

    class ImageRow(Base):
        __tablename__ = "images"
        __table_args__ = {"extend_existing": True}
        id = IDColumn("id")
        name = sa.Column("name", sa.String, nullable=False, index=True)
        project = sa.Column("project", sa.String, nullable=True)
        image = sa.Column("image", sa.String, nullable=False, index=True)
        created_at = sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            index=True,
        )
        tag = sa.Column("tag", sa.TEXT)
        registry = sa.Column("registry", sa.String, nullable=False, index=True)
        registry_id = sa.Column("registry_id", GUID, nullable=False, index=True)
        architecture = sa.Column(
            "architecture", sa.String, nullable=False, index=True, default="x86_64"
        )
        config_digest = sa.Column("config_digest", sa.CHAR(length=72), nullable=False)
        size_bytes = sa.Column("size_bytes", sa.BigInteger, nullable=False)
        is_local = sa.Column(
            "is_local",
            sa.Boolean,
            nullable=False,
            server_default=sa.sql.expression.false(),
        )
        type = sa.Column("type", sa.Enum(ImageType), nullable=False)
        accelerators = sa.Column("accelerators", sa.String)
        labels = sa.Column("labels", sa.JSON, nullable=False, default=dict)
        resources = sa.Column(
            "resources",
            StructuredJSONColumn(
                t.Mapping(
                    t.String,
                    t.Dict({
                        t.Key("min"): t.String,
                        t.Key("max", default=None): t.Null | t.String,
                    }),
                ),
            ),
            nullable=False,
        )

    return ImageRow


def upgrade():
    op.add_column("images", sa.Column("project", sa.String, nullable=True))

    ImageRow = get_image_row_schema()
    ContainerRegistryRow = get_container_registry_row_schema()

    update_stmt = (
        sa.update(ImageRow)
        .values(project=ContainerRegistryRow.project)
        .where(ImageRow.registry_id == ContainerRegistryRow.id)
    )

    op.get_bind().execute(update_stmt)


def downgrade():
    op.drop_column("images", "project")
