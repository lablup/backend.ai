from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.runtime_variant import (
    RuntimeVariantID,
)
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PurgeEntityOpsAction
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.models.runtime_variant.purgers import RuntimeVariantPurger
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow


@dataclass
class PurgeRuntimeVariantAction(PurgeEntityOpsAction[RuntimeVariantRow, RuntimeVariantData]):
    """Remove a runtime variant from the catalog.

    Purge-shaped: the table carries no lifecycle column, so deleting one has
    always been the row leaving the table.
    """

    id: RuntimeVariantID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_runtime_variant"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.to_purger().entity_id()

    @override
    def to_purger(self) -> RuntimeVariantPurger:
        return RuntimeVariantPurger(variant_id=self.id)
