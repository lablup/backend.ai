from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.runtime_variant import RUNTIME_VARIANT_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.identifier.runtime_variant import RuntimeVariantID
from ai.backend.manager.actions.v2.ops.base import PurgeGlobalOpsAction
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.models.runtime_variant.purgers import RuntimeVariantPurger
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow


@dataclass
class DeleteRuntimeVariantAction(PurgeGlobalOpsAction[RuntimeVariantRow, RuntimeVariantData]):
    """Remove a runtime variant from the catalog.

    Purge-shaped: the table carries no lifecycle column, so deleting one has
    always been the row leaving the table.
    """

    id: RuntimeVariantID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RUNTIME_VARIANT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_runtime_variant"

    @override
    def to_purger(self) -> RuntimeVariantPurger:
        return RuntimeVariantPurger(variant_id=self.id)
