"""What a runtime variant search can filter and order by.

Reading a runtime variant costs no permission (the entity is wired public), so another
entity may correlate to it. ``to_data`` stays on the row until this entity is migrated.
"""

from __future__ import annotations

from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.field import SearchableField


class _RuntimeVariantOwnFields:
    """The runtime variant's own columns.

    ``description`` is ``sa.Text`` with no index serving partial matches, and
    ``default_model_definition`` is JSON.
    """

    entity_id = SearchableField(
        RuntimeVariantRow.id,
        UUIDConditions(RuntimeVariantRow.id),
        ColumnOrder(RuntimeVariantRow.id),
    )
    name = SearchableField(
        RuntimeVariantRow.name,
        StringConditions(RuntimeVariantRow.name),
        ColumnOrder(RuntimeVariantRow.name),
    )
    reads_vfolder_config_files = SearchableField(
        RuntimeVariantRow.reads_vfolder_config_files,
        BoolConditions(RuntimeVariantRow.reads_vfolder_config_files),
        ColumnOrder(RuntimeVariantRow.reads_vfolder_config_files),
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
    description = SearchableField(RuntimeVariantRow.description, None, None)
    default_model_definition = SearchableField(
        RuntimeVariantRow.default_model_definition, None, None
    )


class RuntimeVariantSearchableFields:
    own = _RuntimeVariantOwnFields
