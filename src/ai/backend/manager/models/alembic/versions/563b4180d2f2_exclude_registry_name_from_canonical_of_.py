"""Exclude ContainerRegistryRow.registry_name from image canonical name of local type images

Revision ID: 563b4180d2f2
Revises: 6e44ea67d26e
Create Date: 2024-11-29 01:32:55.574036

"""

import enum
import logging

import sqlalchemy as sa
import trafaret as t
from alembic import op
from sqlalchemy.orm import registry

from ai.backend.manager.models.base import (
    GUID,
    IDColumn,
    StrEnumType,
    StructuredJSONColumn,
    convention,
)

# revision identifiers, used by Alembic.
revision = "563b4180d2f2"
down_revision = "6e44ea67d26e"
branch_labels = None
depends_on = None

logger = logging.getLogger("alembic.runtime.migration")

metadata = sa.MetaData(naming_convention=convention)
mapper_registry = registry(metadata=metadata)
Base = mapper_registry.generate_base()


class ContainerRegistryType(enum.StrEnum):
    DOCKER = "docker"
    HARBOR = "harbor"
    HARBOR2 = "harbor2"
    GITHUB = "github"
    GITLAB = "gitlab"
    ECR = "ecr"
    ECR_PUB = "ecr-public"
    LOCAL = "local"


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
        project = sa.Column("project", sa.String(length=255), nullable=True)
        username = sa.Column("username", sa.String(length=255), nullable=True)
        password = sa.Column("password", sa.String, nullable=True)
        ssl_verify = sa.Column("ssl_verify", sa.Boolean, server_default=sa.text("true"), index=True)
        is_global = sa.Column("is_global", sa.Boolean, server_default=sa.text("true"), index=True)
        extra = sa.Column("extra", sa.JSON, nullable=True, default=None)

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


def upgrade() -> None:
    db_connection = op.get_bind()

    ImageRow = get_image_row_schema()
    ContainerRegistryRow = get_container_registry_row_schema()

    update_stmt = (
        sa.update(ImageRow)
        .values(image=sa.func.substring(ImageRow.name, 1, sa.func.strpos(ImageRow.name, ":") - 1))
        .where(ImageRow.is_local == sa.true())
        .returning(ImageRow.id)
    )

    result = db_connection.execute(update_stmt)
    updated_image_ids = [row.id for row in result]

    local_registry_id = db_connection.execute(
        sa.select([ContainerRegistryRow.id]).where(
            sa.and_(
                ContainerRegistryRow.type == ContainerRegistryType.LOCAL,
            )
        )
    ).scalar_one_or_none()

    local_registry_info = {
        "type": ContainerRegistryType.LOCAL,
        "registry_name": "local",
        # url is not used for local registry.
        # but it is required in the old schema (etcd),
        # so, let's put a dummy value for compatibility purposes.
        "url": "http://localhost",
    }

    if not local_registry_id:
        local_registry_id = db_connection.execute(
            sa.insert(ContainerRegistryRow)
            .values(**local_registry_info)
            .returning(ContainerRegistryRow.id)
        ).scalar_one()

    # Ensure that local images point to the local registry.
    update_registry_stmt = (
        sa.update(ImageRow)
        .where(ImageRow.id.in_(updated_image_ids))
        .values(registry_id=local_registry_id)
    )

    db_connection.execute(update_registry_stmt)


def downgrade() -> None:
    # TODO:
    # Since the range of possible local type images has expanded,
    # It is not possible to perform a proper downgrade here.
    pass
