"""exclude registry_name from canonical of local type images

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

from ai.backend.manager.models.base import GUID, IDColumn, StructuredJSONColumn, convention

# revision identifiers, used by Alembic.
revision = "563b4180d2f2"
down_revision = "6e44ea67d26e"
branch_labels = None
depends_on = None

logger = logging.getLogger("alembic.runtime.migration")

metadata = sa.MetaData(naming_convention=convention)
mapper_registry = registry(metadata=metadata)
Base = mapper_registry.generate_base()


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
    ImageRow = get_image_row_schema()

    update_stmt = (
        sa.update(ImageRow)
        .values(image=sa.func.substring(ImageRow.name, 1, sa.func.strpos(ImageRow.name, ":") - 1))
        .where(ImageRow.is_local == sa.true())
    )

    op.get_bind().execute(update_stmt)


def downgrade() -> None:
    # TODO:
    # Since the range of possible local type images has expanded,
    # It is not possible to perform a proper downgrade here.
    pass
