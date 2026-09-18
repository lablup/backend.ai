"""The vfolder fields a search can filter and order by."""

from __future__ import annotations

from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.types import VFolderUsageMode
from ai.backend.manager.data.vfolder.types import VFolderOperationStatus
from ai.backend.manager.models.entity_label.searchable_fields import (
    EntityLabelCorrelation,
    EntityLabelSearchableFields,
)
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.membership import MembershipConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.field import NestedSearchableField, SearchableField
from ai.backend.manager.models.vfolder.row import VFolderRow


class VFolderSearchableFields:
    id = SearchableField(UUIDConditions(VFolderRow.id), ColumnOrder(VFolderRow.id))
    name = SearchableField(StringConditions(VFolderRow.name), ColumnOrder(VFolderRow.name))
    host = SearchableField(StringConditions(VFolderRow.host), ColumnOrder(VFolderRow.host))
    status = SearchableField(
        EnumConditions(VFolderRow.status, VFolderOperationStatus), ColumnOrder(VFolderRow.status)
    )
    usage_mode = SearchableField(
        EnumConditions(VFolderRow.usage_mode, VFolderUsageMode),
        ColumnOrder(VFolderRow.usage_mode),
    )
    cloneable = SearchableField(BoolConditions(VFolderRow.cloneable), None)
    created_at = SearchableField(
        DateTimeConditions(VFolderRow.created_at), ColumnOrder(VFolderRow.created_at)
    )
    membership = SearchableField(MembershipConditions(VFolderEntityType(), VFolderRow.id), None)
    labels = NestedSearchableField(
        EntityLabelSearchableFields,
        EntityLabelCorrelation(VFolderRow, VFolderEntityType(), VFolderRow.id),
    )
