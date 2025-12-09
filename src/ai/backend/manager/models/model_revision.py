import logging
import uuid
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.orm import foreign, relationship

from ai.backend.common.types import ClusterMode, RuntimeVariant, VFolderMount
from ai.backend.logging import BraceStyleAdapter

from .base import (
    GUID,
    Base,
    IDColumn,
    ResourceSlotColumn,
    StrEnumType,
    StructuredJSONObjectListColumn,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("ModelRevisionRow",)


def _get_model_revision_deployment_join_cond():
    from .model_deployment import ModelDeploymentRow

    return foreign(ModelRevisionRow.model_deployment_id) == ModelDeploymentRow.id


def _get_model_vfolder_revision_join_cond():
    from .vfolder import VFolderRow

    return foreign(ModelRevisionRow.model_vfolder_id) == VFolderRow.id


def _get_image_revision_join_cond():
    from .image import ImageRow

    return foreign(ModelRevisionRow.image_id) == ImageRow.id


class ModelRevisionRow(Base):
    __tablename__ = "model_revisions"

    id = IDColumn("id")

    name = sa.Column("name", sa.String, nullable=False)
    model_deployment_id = sa.Column(
        "model_deployment_id",
        GUID,
        nullable=False,
    )
    tags = sa.Column("tags", sa.TEXT, nullable=False, default="")
    runtime_variant = sa.Column("runtime_variant", StrEnumType(RuntimeVariant), nullable=False)
    inference_runtime_config = sa.Column("inference_runtime_config", pgsql.JSONB, nullable=False)
    environment_variables = sa.Column(
        "environment_variables", pgsql.JSONB, nullable=False, default=dict
    )
    model_vfolder_id = sa.Column(
        "model_vfolder_id",
        GUID,
        nullable=False,
    )
    model_mount_destination = sa.Column(
        "model_mount_destination",
        sa.String,
        nullable=False,
        default="/models",
        server_default="/models",
    )
    model_definition_path = sa.Column("model_definition_path", sa.String, nullable=False)
    image_id = sa.Column(
        "image_id",
        GUID,
        nullable=False,
    )
    cluster_mode = sa.Column(
        "cluster_mode",
        sa.String,
        nullable=False,
        default=ClusterMode.SINGLE_NODE,
        server_default=ClusterMode.SINGLE_NODE,
    )
    cluster_size = sa.Column(
        "cluster_size", sa.Integer, nullable=False, default=1, server_default="1"
    )
    resource_group = sa.Column("resource_group", sa.String, nullable=False)
    resource_slots = sa.Column("resource_slots", ResourceSlotColumn(), nullable=False)
    resource_opts = sa.Column("resource_opts", pgsql.JSONB, nullable=False)
    extra_mount = sa.Column(
        "extra_mount",
        StructuredJSONObjectListColumn(VFolderMount),
        nullable=False,
        default=[],
        server_default="[]",
    )
    created_at = sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )

    # Relationships
    model_deployment_row = relationship(
        "ModelDeploymentRow",
        back_populates="revision_rows",
        primaryjoin=_get_model_revision_deployment_join_cond,
    )
    model_vfolder_row = relationship(
        "VFolderRow",
        primaryjoin=_get_model_vfolder_revision_join_cond,
    )
    image_row = relationship(
        "ImageRow",
        primaryjoin=_get_image_revision_join_cond,
    )

    def __init__(
        self,
        name: str,
        model_deployment_id: uuid.UUID,
        tags: str,
        runtime_variant: str,
        inference_runtime_config: dict,
        environment_variables: dict,
        model_vfolder_id: uuid.UUID,
        model_mount_destination: str,
        model_definition_path: str,
        image: uuid.UUID,
        cluster_mode: str,
        cluster_size: int,
        resource_group: str,
        resource_slots: dict,
        resource_opts: dict,
        extra_mount: dict,
        created_at: Optional[datetime] = None,
    ):
        self.name = name
        self.model_deployment_id = model_deployment_id
        self.tags = tags
        self.runtime_variant = runtime_variant
        self.inference_runtime_config = inference_runtime_config
        self.environment_variables = environment_variables
        self.model_vfolder_id = model_vfolder_id
        self.model_mount_destination = model_mount_destination
        self.model_definition_path = model_definition_path
        self.image = image
        self.created_at = created_at
        self.cluster_mode = cluster_mode
        self.cluster_size = cluster_size
        self.resource_group = resource_group
        self.resource_slots = resource_slots
        self.resource_opts = resource_opts
        self.extra_mount = extra_mount

    def __str__(self) -> str:
        return (
            f"ModelRevisionRow("
            f"id: {self.id}, "
            f"name: {self.name}, "
            f"model_deployment_id: {self.model_deployment_id}, "
            f"runtime_variant: {self.runtime_variant}, "
            f"created_at: {self.created_at}"
            f")"
        )

    def __repr__(self) -> str:
        return self.__str__()
