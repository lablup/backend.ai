"""What an image search can filter and order by, and how an image row becomes data."""

from __future__ import annotations

from decimal import Decimal
from typing import override

import sqlalchemy as sa

from ai.backend.common.data.entity.deployment import DeploymentID
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
from ai.backend.manager.models.specs.search.field import NestedSearchableField, SearchableField
from ai.backend.manager.models.specs.search.usage import UsageConditions


class _ImageOwnFields(RowDataConverter[ImageRow, ImageData]):
    """The image's own columns.

    ``labels`` is JSON, so both slots stay empty. ``resources``, ``resource_limits`` and
    ``tags`` are derived — the row folds the column together with the labels, or reads the
    canonical name apart — so they carry no field and are built in :meth:`to_data`.
    """

    id = SearchableField(ImageRow.id, UUIDConditions(ImageRow.id), ColumnOrder(ImageRow.id))
    name = SearchableField(
        ImageRow.name, StringConditions(ImageRow.name), ColumnOrder(ImageRow.name)
    )
    project = SearchableField(
        ImageRow.project, StringConditions(ImageRow.project), ColumnOrder(ImageRow.project)
    )
    image = SearchableField(
        ImageRow.image, StringConditions(ImageRow.image), ColumnOrder(ImageRow.image)
    )
    tag = SearchableField(ImageRow.tag, StringConditions(ImageRow.tag), ColumnOrder(ImageRow.tag))
    registry = SearchableField(
        ImageRow.registry, StringConditions(ImageRow.registry), ColumnOrder(ImageRow.registry)
    )
    registry_id = SearchableField(
        ImageRow.registry_id,
        UUIDConditions(ImageRow.registry_id),
        ColumnOrder(ImageRow.registry_id),
    )
    architecture = SearchableField(
        ImageRow.architecture,
        StringConditions(ImageRow.architecture),
        ColumnOrder(ImageRow.architecture),
    )
    config_digest = SearchableField(
        ImageRow.config_digest,
        StringConditions(ImageRow.config_digest),
        ColumnOrder(ImageRow.config_digest),
    )
    size_bytes = SearchableField(
        ImageRow.size_bytes, IntConditions(ImageRow.size_bytes), ColumnOrder(ImageRow.size_bytes)
    )
    is_local = SearchableField(
        ImageRow.is_local, BoolConditions(ImageRow.is_local), ColumnOrder(ImageRow.is_local)
    )
    type = SearchableField(
        ImageRow.type, EnumConditions(ImageRow.type, ImageType), ColumnOrder(ImageRow.type)
    )
    accelerators = SearchableField(
        ImageRow.accelerators,
        StringConditions(ImageRow.accelerators),
        ColumnOrder(ImageRow.accelerators),
    )
    labels = SearchableField(ImageRow.labels, None, None)
    customized = SearchableField(
        ImageRow.customized, BoolConditions(ImageRow.customized), ColumnOrder(ImageRow.customized)
    )
    creator_id = SearchableField(
        ImageRow.creator_id, UUIDConditions(ImageRow.creator_id), ColumnOrder(ImageRow.creator_id)
    )
    status = SearchableField(
        ImageRow.status,
        EnumConditions(ImageRow.status, ImageStatus),
        ColumnOrder(ImageRow.status),
    )
    created_at = SearchableField(
        ImageRow.created_at,
        DateTimeConditions(ImageRow.created_at),
        ColumnOrder(ImageRow.created_at),
    )
    last_used_at = SearchableField(
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


class _ImageAliasOwnFields(RowDataConverter[ImageAliasRow, ImageAliasData]):
    """An alias row's own columns."""

    id = SearchableField(
        ImageAliasRow.id, UUIDConditions(ImageAliasRow.id), ColumnOrder(ImageAliasRow.id)
    )
    alias = SearchableField(
        ImageAliasRow.alias,
        StringConditions(ImageAliasRow.alias),
        ColumnOrder(ImageAliasRow.alias),
    )
    image_id = SearchableField(
        ImageAliasRow.image_id,
        UUIDConditions(ImageAliasRow.image_id),
        ColumnOrder(ImageAliasRow.image_id),
    )

    @override
    def to_data(self, row: ImageAliasRow) -> ImageAliasData:
        return ImageAliasData(id=ImageAliasID(self.id.read(row)), alias=self.alias.read(row) or "")


class ImageAliasSearchableFields:
    own = _ImageAliasOwnFields()


class _ImageNestedFields:
    """Rows of other tables the image owns: its aliases."""

    aliases = NestedSearchableField(
        ImageAliasSearchableFields.own,
        ToManyCorrelation(ImageAliasRow, ImageRow, ImageAliasRow.image_id == ImageRow.id),
    )


class _ImageLinkedEntities:
    """How an image connects to other entities; the other entity's permission governs."""

    sessions = UsageConditions[SessionID](
        ToManyCorrelation(KernelRow, ImageRow, KernelRow.image_id == ImageRow.id),
        KernelRow.session_id,
    )
    """Images a session's kernels run."""
    deployments = UsageConditions[DeploymentID](
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


class ImageSearchableFields:
    own = _ImageOwnFields()
    nested = _ImageNestedFields
    linked = _ImageLinkedEntities
