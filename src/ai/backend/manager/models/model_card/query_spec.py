"""What a model card search can filter and order by, and how a model card row becomes data."""

from __future__ import annotations

from decimal import Decimal
from typing import override

from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.manager.data.model_card.types import (
    ModelCardData,
    ModelCardResourceRequirementData,
)
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.resource_slot.row import ModelCardResourceRequirementRow
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.number import DecimalConditions
from ai.backend.manager.models.specs.conditions.string import (
    StringConditions,
    StringEqualityConditions,
)
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.correlation import ToManyCorrelation
from ai.backend.manager.models.specs.search.field import NestedQueryColumn, QueryColumn
from ai.backend.manager.models.specs.search.usage import UsesConditions
from ai.backend.manager.models.vfolder.row import VFolderRow


class _ModelCardOwnColumns(RowDataConverter[ModelCardRow, ModelCardData]):
    """The model card's own columns."""

    id = QueryColumn(ModelCardRow.id, UUIDConditions(ModelCardRow.id), ColumnOrder(ModelCardRow.id))
    name = QueryColumn(
        ModelCardRow.name, StringConditions(ModelCardRow.name), ColumnOrder(ModelCardRow.name)
    )
    vfolder_id = QueryColumn(
        ModelCardRow.vfolder,
        UUIDConditions(ModelCardRow.vfolder),
        ColumnOrder(ModelCardRow.vfolder),
    )
    domain = QueryColumn(
        ModelCardRow.domain, StringConditions(ModelCardRow.domain), ColumnOrder(ModelCardRow.domain)
    )
    project_id = QueryColumn(
        ModelCardRow.project,
        UUIDConditions(ModelCardRow.project),
        ColumnOrder(ModelCardRow.project),
    )
    creator_id = QueryColumn(
        ModelCardRow.creator,
        UUIDConditions(ModelCardRow.creator),
        ColumnOrder(ModelCardRow.creator),
    )
    author = QueryColumn(
        ModelCardRow.author, StringConditions(ModelCardRow.author), ColumnOrder(ModelCardRow.author)
    )
    title = QueryColumn(
        ModelCardRow.title, StringConditions(ModelCardRow.title), ColumnOrder(ModelCardRow.title)
    )
    model_version = QueryColumn(
        ModelCardRow.model_version,
        StringConditions(ModelCardRow.model_version),
        ColumnOrder(ModelCardRow.model_version),
    )
    description = QueryColumn(
        ModelCardRow.description,
        StringEqualityConditions(ModelCardRow.description),
        ColumnOrder(ModelCardRow.description),
    )
    task = QueryColumn(
        ModelCardRow.task, StringConditions(ModelCardRow.task), ColumnOrder(ModelCardRow.task)
    )
    category = QueryColumn(
        ModelCardRow.category,
        StringConditions(ModelCardRow.category),
        ColumnOrder(ModelCardRow.category),
    )
    architecture = QueryColumn(
        ModelCardRow.architecture,
        StringConditions(ModelCardRow.architecture),
        ColumnOrder(ModelCardRow.architecture),
    )
    framework = QueryColumn(ModelCardRow.framework, None, None)
    label = QueryColumn(ModelCardRow.label, None, None)
    license = QueryColumn(
        ModelCardRow.license,
        StringConditions(ModelCardRow.license),
        ColumnOrder(ModelCardRow.license),
    )
    readme = QueryColumn(
        ModelCardRow.readme,
        StringEqualityConditions(ModelCardRow.readme),
        ColumnOrder(ModelCardRow.readme),
    )
    access_level = QueryColumn(
        ModelCardRow.access_level,
        StringConditions(ModelCardRow.access_level),
        ColumnOrder(ModelCardRow.access_level),
    )
    created_at = QueryColumn(
        ModelCardRow.created_at,
        DateTimeConditions(ModelCardRow.created_at),
        ColumnOrder(ModelCardRow.created_at),
    )
    updated_at = QueryColumn(
        ModelCardRow.updated_at,
        DateTimeConditions(ModelCardRow.updated_at),
        ColumnOrder(ModelCardRow.updated_at),
    )

    @override
    def to_data(self, row: ModelCardRow) -> ModelCardData:
        """Project this row.

        The minimum resource requirements live in their own table and are not read
        here: reaching into a child table would force an eager load on every read.
        """
        return ModelCardData(
            id=self.id.read(row),
            name=self.name.read(row),
            vfolder_id=self.vfolder_id.read(row),
            domain=self.domain.read(row),
            project_id=self.project_id.read(row),
            creator_id=self.creator_id.read(row),
            author=self.author.read(row),
            title=self.title.read(row),
            model_version=self.model_version.read(row),
            description=self.description.read(row),
            task=self.task.read(row),
            category=self.category.read(row),
            architecture=self.architecture.read(row),
            framework=self.framework.read(row),
            label=self.label.read(row),
            license=self.license.read(row),
            readme=self.readme.read(row),
            access_level=self.access_level.read(row),
            created_at=self.created_at.read(row),
            updated_at=self.updated_at.read(row),
        )


class _ModelCardResourceRequirementOwnColumns(
    RowDataConverter[ModelCardResourceRequirementRow, ModelCardResourceRequirementData]
):
    """A minimum-quantity row's own columns."""

    model_card_id = QueryColumn(
        ModelCardResourceRequirementRow.model_card_id,
        UUIDConditions(ModelCardResourceRequirementRow.model_card_id),
        ColumnOrder(ModelCardResourceRequirementRow.model_card_id),
    )
    slot_name = QueryColumn(
        ModelCardResourceRequirementRow.slot_name,
        StringConditions(ModelCardResourceRequirementRow.slot_name),
        ColumnOrder(ModelCardResourceRequirementRow.slot_name),
    )
    min_quantity = QueryColumn(
        ModelCardResourceRequirementRow.min_quantity,
        DecimalConditions(ModelCardResourceRequirementRow.min_quantity),
        ColumnOrder(ModelCardResourceRequirementRow.min_quantity),
    )

    @override
    def to_data(self, row: ModelCardResourceRequirementRow) -> ModelCardResourceRequirementData:
        return ModelCardResourceRequirementData(
            model_card_id=self.model_card_id.read(row),
            slot_name=self.slot_name.read(row),
            min_quantity=self._format(self.min_quantity.read(row)),
        )

    def _format(self, value: Decimal | str) -> str:
        """The quantity as the caller wrote it, not as ``Numeric(24, 6)`` stores it.

        A read of ``"2"`` comes back ``Decimal("2.000000")``; before a flush the
        attribute may still be the raw string, so normalize before trimming.
        """
        quantity = value if isinstance(value, Decimal) else Decimal(value)
        if quantity == quantity.to_integral_value():
            return str(int(quantity))
        return format(quantity.normalize(), "f")


class ModelCardResourceRequirementQuerySpec:
    own = _ModelCardResourceRequirementOwnColumns()


class _ModelCardNestedColumns:
    """The rows the model card owns. Read under the model card's own permission."""

    min_resource = NestedQueryColumn(
        ModelCardResourceRequirementQuerySpec.own,
        ToManyCorrelation(
            ModelCardResourceRequirementRow,
            ModelCardRow,
            ModelCardResourceRequirementRow.model_card_id == ModelCardRow.id,
        ),
    )


class _ModelCardUsage:
    """Uses between a model card and other entities."""

    vfolders = UsesConditions[VFolderUUID](
        ToManyCorrelation(VFolderRow, ModelCardRow, VFolderRow.id == ModelCardRow.vfolder),
        VFolderRow.id,
    )
    """Model cards built on the vfolder.

    The same foreign key answers the vfolder side's ``usage.model_cards``.
    """


class _ModelCardLinkedEntities:
    """How a model card connects to other entities; the other entity's permission governs."""

    usage = _ModelCardUsage


class ModelCardQuerySpec:
    own = _ModelCardOwnColumns()
    nested = _ModelCardNestedColumns
    linked = _ModelCardLinkedEntities
