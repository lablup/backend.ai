"""DataLookup implementations for the runtime variant repository."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.specs.lookup import DataLookup


@dataclass
class RuntimeVariantLookup(DataLookup[RuntimeVariantRow, RuntimeVariantID]):
    """Resolves a runtime variant's name into the row it names.

    The name is unique, which separates this from a search: two matches would mean the
    constraint is missing.
    """

    name: str

    @override
    def row_class(self) -> type[RuntimeVariantRow]:
        return RuntimeVariantRow

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [lambda: RuntimeVariantRow.name == self.name]

    @override
    def to_entity_id(self, row: RuntimeVariantRow) -> RuntimeVariantID:
        return row.id
