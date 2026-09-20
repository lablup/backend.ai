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
from ai.backend.manager.models.specs.search.field import NestedSearchableField, SearchableField
from ai.backend.manager.models.specs.search.usage import UsageConditions
from ai.backend.manager.models.vfolder.row import VFolderRow


class _ModelCardOwnFields(RowDataConverter[ModelCardRow, ModelCardData]):
    """The model card's own columns."""

    id = SearchableField(
        ModelCardRow.id, UUIDConditions(ModelCardRow.id), ColumnOrder(ModelCardRow.id)
    )
    name = SearchableField(
        ModelCardRow.name, StringConditions(ModelCardRow.name), ColumnOrder(ModelCardRow.name)
    )
    vfolder_id = SearchableField(
        ModelCardRow.vfolder,
        UUIDConditions(ModelCardRow.vfolder),
        ColumnOrder(ModelCardRow.vfolder),
    )
    domain = SearchableField(
        ModelCardRow.domain, StringConditions(ModelCardRow.domain), ColumnOrder(ModelCardRow.domain)
    )
    project_id = SearchableField(
        ModelCardRow.project,
        UUIDConditions(ModelCardRow.project),
        ColumnOrder(ModelCardRow.project),
    )
    creator_id = SearchableField(
        ModelCardRow.creator,
        UUIDConditions(ModelCardRow.creator),
        ColumnOrder(ModelCardRow.creator),
    )
    author = SearchableField(
        ModelCardRow.author, StringConditions(ModelCardRow.author), ColumnOrder(ModelCardRow.author)
    )
    title = SearchableField(
        ModelCardRow.title, StringConditions(ModelCardRow.title), ColumnOrder(ModelCardRow.title)
    )
    model_version = SearchableField(
        ModelCardRow.model_version,
        StringConditions(ModelCardRow.model_version),
        ColumnOrder(ModelCardRow.model_version),
    )
    description = SearchableField(
        ModelCardRow.description,
        StringEqualityConditions(ModelCardRow.description),
        ColumnOrder(ModelCardRow.description),
    )
    task = SearchableField(
        ModelCardRow.task, StringConditions(ModelCardRow.task), ColumnOrder(ModelCardRow.task)
    )
    category = SearchableField(
        ModelCardRow.category,
        StringConditions(ModelCardRow.category),
        ColumnOrder(ModelCardRow.category),
    )
    architecture = SearchableField(
        ModelCardRow.architecture,
        StringConditions(ModelCardRow.architecture),
        ColumnOrder(ModelCardRow.architecture),
    )
    framework = SearchableField(ModelCardRow.framework, None, None)
    label = SearchableField(ModelCardRow.label, None, None)
    license = SearchableField(
        ModelCardRow.license,
        StringConditions(ModelCardRow.license),
        ColumnOrder(ModelCardRow.license),
    )
    readme = SearchableField(
        ModelCardRow.readme,
        StringEqualityConditions(ModelCardRow.readme),
        ColumnOrder(ModelCardRow.readme),
    )
    access_level = SearchableField(
        ModelCardRow.access_level,
        StringConditions(ModelCardRow.access_level),
        ColumnOrder(ModelCardRow.access_level),
    )
    created_at = SearchableField(
        ModelCardRow.created_at,
        DateTimeConditions(ModelCardRow.created_at),
        ColumnOrder(ModelCardRow.created_at),
    )
    updated_at = SearchableField(
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


class _ModelCardResourceRequirementOwnFields(
    RowDataConverter[ModelCardResourceRequirementRow, ModelCardResourceRequirementData]
):
    """A minimum-quantity row's own columns."""

    model_card_id = SearchableField(
        ModelCardResourceRequirementRow.model_card_id,
        UUIDConditions(ModelCardResourceRequirementRow.model_card_id),
        ColumnOrder(ModelCardResourceRequirementRow.model_card_id),
    )
    slot_name = SearchableField(
        ModelCardResourceRequirementRow.slot_name,
        StringConditions(ModelCardResourceRequirementRow.slot_name),
        ColumnOrder(ModelCardResourceRequirementRow.slot_name),
    )
    min_quantity = SearchableField(
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


class ModelCardResourceRequirementSearchableFields:
    own = _ModelCardResourceRequirementOwnFields()


class _ModelCardNestedFields:
    """The rows the model card owns. Read under the model card's own permission."""

    min_resource = NestedSearchableField(
        ModelCardResourceRequirementSearchableFields.own,
        ToManyCorrelation(
            ModelCardResourceRequirementRow,
            ModelCardRow,
            ModelCardResourceRequirementRow.model_card_id == ModelCardRow.id,
        ),
    )


class _ModelCardLinkedEntities:
    """How a model card connects to other entities; the other entity's permission governs."""

    vfolders = UsageConditions[VFolderUUID](
        ToManyCorrelation(VFolderRow, ModelCardRow, VFolderRow.id == ModelCardRow.vfolder),
        VFolderRow.id,
    )
    """The vfolder a card names as its model.

    Read the other way round from the vfolder side's ``model_cards``: there the card is
    the using entity, here the vfolder is what is named. Both answer over the same
    foreign key, and both require the caller to read the entity they name.
    """


class ModelCardSearchableFields:
    own = _ModelCardOwnFields()
    nested = _ModelCardNestedFields
    linked = _ModelCardLinkedEntities
