from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.identifier.runtime_variant import RuntimeVariantID
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.specs.purger import EntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class RuntimeVariantPurger(EntityPurger[RuntimeVariantRow, RuntimeVariantData]):
    """Purger for removing a runtime variant from the catalog."""

    variant_id: RuntimeVariantID

    @override
    def row_class(self) -> type[RuntimeVariantRow]:
        return RuntimeVariantRow

    @override
    def pk_value(self) -> RuntimeVariantID:
        return self.variant_id

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.variant_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: RuntimeVariantRow) -> RuntimeVariantData:
        return row.to_data()
