"""What an image search can filter and order by, and how an image row becomes data."""

from __future__ import annotations

from decimal import Decimal
from typing import override

import sqlalchemy as sa

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.image import ImageEntityType
from ai.backend.common.data.entity.image_alias import ImageAliasID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.types import ImageCanonical
from ai.backend.manager.data.deployment.types import ReplicaGroupLifecycle
from ai.backend.manager.data.image.types import (
    ImageAliasData,
    ImageData,
    ImageLabelsData,
    ImageResourcesData,
    ImageStatus,
    ImageTagEntry,
    ImageType,
    ResourceLimit,
)
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.entity_label.query_spec import (
    EntityLabelCorrelation,
    EntityLabelQuerySpec,
)
from ai.backend.manager.models.image.row import ImageAliasRow, ImageRow
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.replica_group.row import ReplicaGroupRow
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.integer import IntConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.correlation import ToManyCorrelation
from ai.backend.manager.models.specs.search.field import NestedQueryColumn, QueryColumn
from ai.backend.manager.models.specs.search.usage import UsedByConditions


class _ImageOwnColumns(RowDataConverter[ImageRow, ImageData]):
    """The image's own columns.

    ``labels`` is JSON, so both slots stay empty. ``resources``, ``resource_limits`` and
    ``tags`` are derived — the row folds the column together with the labels, or reads the
    canonical name apart — so they carry no field and are built in :meth:`to_data`.
    """

    id = QueryColumn(ImageRow.id, UUIDConditions(ImageRow.id), ColumnOrder(ImageRow.id))
    name = QueryColumn(ImageRow.name, StringConditions(ImageRow.name), ColumnOrder(ImageRow.name))
    project = QueryColumn(
        ImageRow.project, StringConditions(ImageRow.project), ColumnOrder(ImageRow.project)
    )
    image = QueryColumn(
        ImageRow.image, StringConditions(ImageRow.image), ColumnOrder(ImageRow.image)
    )
    tag = QueryColumn(ImageRow.tag, StringConditions(ImageRow.tag), ColumnOrder(ImageRow.tag))
    registry = QueryColumn(
        ImageRow.registry, StringConditions(ImageRow.registry), ColumnOrder(ImageRow.registry)
    )
    registry_id = QueryColumn(
        ImageRow.registry_id,
        UUIDConditions(ImageRow.registry_id),
        ColumnOrder(ImageRow.registry_id),
    )
    architecture = QueryColumn(
        ImageRow.architecture,
        StringConditions(ImageRow.architecture),
        ColumnOrder(ImageRow.architecture),
    )
    config_digest = QueryColumn(
        ImageRow.config_digest,
        StringConditions(ImageRow.config_digest),
        ColumnOrder(ImageRow.config_digest),
    )
    size_bytes = QueryColumn(
        ImageRow.size_bytes, IntConditions(ImageRow.size_bytes), ColumnOrder(ImageRow.size_bytes)
    )
    is_local = QueryColumn(
        ImageRow.is_local, BoolConditions(ImageRow.is_local), ColumnOrder(ImageRow.is_local)
    )
    type = QueryColumn(
        ImageRow.type, EnumConditions(ImageRow.type, ImageType), ColumnOrder(ImageRow.type)
    )
    accelerators = QueryColumn(
        ImageRow.accelerators,
        StringConditions(ImageRow.accelerators),
        ColumnOrder(ImageRow.accelerators),
    )
    labels = QueryColumn(ImageRow.labels, None, None)
    customized = QueryColumn(
        ImageRow.customized, BoolConditions(ImageRow.customized), ColumnOrder(ImageRow.customized)
    )
    creator_id = QueryColumn(
        ImageRow.creator_id, UUIDConditions(ImageRow.creator_id), ColumnOrder(ImageRow.creator_id)
    )
    status = QueryColumn(
        ImageRow.status,
        EnumConditions(ImageRow.status, ImageStatus),
        ColumnOrder(ImageRow.status),
    )
    created_at = QueryColumn(
        ImageRow.created_at,
        DateTimeConditions(ImageRow.created_at),
        ColumnOrder(ImageRow.created_at),
    )
    last_used_at = QueryColumn(
        ImageRow.last_used_at,
        DateTimeConditions(ImageRow.last_used_at),
        ColumnOrder(ImageRow.last_used_at),
    )

    @override
    def to_data(self, row: ImageRow) -> ImageData:
        _, tag_set = row.image_ref.tag_set
        resources = row.resources
        return ImageData(
            id=self.id.read(row),
            name=ImageCanonical(self.name.read(row)),
            project=self.project.read(row),
            image=self.image.read(row),
            created_at=self.created_at.read(row),
            tag=self.tag.read(row),
            registry=self.registry.read(row),
            registry_id=self.registry_id.read(row),
            architecture=self.architecture.read(row),
            config_digest=self.config_digest.read(row).strip(),
            size_bytes=self.size_bytes.read(row),
            is_local=self.is_local.read(row),
            type=self.type.read(row),
            accelerators=self.accelerators.read(row),
            labels=ImageLabelsData(label_data=self.labels.read(row)),
            resources=ImageResourcesData(resources_data=resources),
            resource_limits=[
                ResourceLimit(
                    key=str(key),
                    min=spec.get("min", Decimal(0)),
                    max=spec.get("max", Decimal("Infinity")),
                )
                for key, spec in resources.items()
            ],
            tags=[ImageTagEntry(key=key, value=value) for key, value in tag_set.items()],
            status=self.status.read(row),
            customized=self.customized.read(row),
            creator_id=self.creator_id.read(row),
            last_used_at=self.last_used_at.read(row),
        )


class _ImageAliasOwnColumns(RowDataConverter[ImageAliasRow, ImageAliasData]):
    """An alias row's own columns."""

    id = QueryColumn(
        ImageAliasRow.id, UUIDConditions(ImageAliasRow.id), ColumnOrder(ImageAliasRow.id)
    )
    alias = QueryColumn(
        ImageAliasRow.alias,
        StringConditions(ImageAliasRow.alias),
        ColumnOrder(ImageAliasRow.alias),
    )
    image_id = QueryColumn(
        ImageAliasRow.image_id,
        UUIDConditions(ImageAliasRow.image_id),
        ColumnOrder(ImageAliasRow.image_id),
    )

    @override
    def to_data(self, row: ImageAliasRow) -> ImageAliasData:
        return ImageAliasData(id=ImageAliasID(self.id.read(row)), alias=self.alias.read(row) or "")


class ImageAliasQuerySpec:
    own = _ImageAliasOwnColumns()


class _ImageNestedColumns:
    """Rows of other tables the image owns: its labels and its aliases."""

    labels = NestedQueryColumn(
        EntityLabelQuerySpec.own,
        EntityLabelCorrelation(ImageRow, ImageEntityType(), ImageRow.id),
    )
    aliases = NestedQueryColumn(
        ImageAliasQuerySpec.own,
        ToManyCorrelation(ImageAliasRow, ImageRow, ImageAliasRow.image_id == ImageRow.id),
    )


class _ImageUsage:
    """Uses between an image and other entities."""

    sessions = UsedByConditions[SessionID](
        ToManyCorrelation(KernelRow, ImageRow, KernelRow.image_id == ImageRow.id),
        KernelRow.session_id,
    )
    """Images a session's kernels run."""
    deployments = UsedByConditions[DeploymentID](
        ToManyCorrelation(
            sa.join(
                ReplicaGroupRow,
                DeploymentRevisionRow,
                DeploymentRevisionRow.id == ReplicaGroupRow.current_revision_id,
            ),
            ImageRow,
            sa.and_(
                ReplicaGroupRow.lifecycle.not_in(ReplicaGroupLifecycle.terminal_statuses()),
                DeploymentRevisionRow.image == ImageRow.id,
            ),
        ),
        ReplicaGroupRow.deployment_id,
    )
    """Images a live replica group's current revision names."""


class _ImageLinkedEntities:
    """How an image connects to other entities; the other entity's permission governs."""

    usage = _ImageUsage


class ImageQuerySpec:
    own = _ImageOwnColumns()
    nested = _ImageNestedColumns
    linked = _ImageLinkedEntities
