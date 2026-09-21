"""What a runtime variant search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.correlation import ToManyCorrelation
from ai.backend.manager.models.specs.search.field import SearchableField
from ai.backend.manager.models.specs.search.usage import UsedByConditions


class _RuntimeVariantOwnFields(RowDataConverter[RuntimeVariantRow, RuntimeVariantData]):
    """The runtime variant's own columns.

    ``description`` is ``sa.Text`` with no index serving partial matches, and
    ``default_model_definition`` is JSON.
    """

    id = SearchableField(
        RuntimeVariantRow.id,
        UUIDConditions(RuntimeVariantRow.id),
        ColumnOrder(RuntimeVariantRow.id),
    )
    name = SearchableField(
        RuntimeVariantRow.name,
        StringConditions(RuntimeVariantRow.name),
        ColumnOrder(RuntimeVariantRow.name),
    )
    description = SearchableField(RuntimeVariantRow.description, None, None)
    reads_vfolder_config_files = SearchableField(
        RuntimeVariantRow.reads_vfolder_config_files,
        BoolConditions(RuntimeVariantRow.reads_vfolder_config_files),
        ColumnOrder(RuntimeVariantRow.reads_vfolder_config_files),
    )
    default_model_definition = SearchableField(
        RuntimeVariantRow.default_model_definition, None, None
    )
    created_at = SearchableField(
        RuntimeVariantRow.created_at,
        DateTimeConditions(RuntimeVariantRow.created_at),
        ColumnOrder(RuntimeVariantRow.created_at),
    )
    updated_at = SearchableField(
        RuntimeVariantRow.updated_at,
        DateTimeConditions(RuntimeVariantRow.updated_at),
        ColumnOrder(RuntimeVariantRow.updated_at),
    )

    @override
    def to_data(self, row: RuntimeVariantRow) -> RuntimeVariantData:
        return RuntimeVariantData(
            id=self.id.read(row),
            name=self.name.read(row),
            description=self.description.read(row),
            reads_vfolder_config_files=self.reads_vfolder_config_files.read(row),
            default_model_definition=self.default_model_definition.read(row),
            created_at=self.created_at.read(row),
            updated_at=self.updated_at.read(row),
        )


class _RuntimeVariantUsage:
    """Uses between a runtime variant and other entities."""

    deployments = UsedByConditions[DeploymentID](
        ToManyCorrelation(
            DeploymentRevisionRow,
            RuntimeVariantRow,
            DeploymentRevisionRow.runtime_variant_id == RuntimeVariantRow.id,
        ),
        DeploymentRevisionRow.endpoint,
    )
    """Runtime variants a deployment's revisions name."""


class _RuntimeVariantLinkedEntities:
    """How a runtime variant connects to other entities; the other entity's permission governs."""

    usage = _RuntimeVariantUsage


class RuntimeVariantSearchableFields:
    own = _RuntimeVariantOwnFields()
    linked = _RuntimeVariantLinkedEntities
