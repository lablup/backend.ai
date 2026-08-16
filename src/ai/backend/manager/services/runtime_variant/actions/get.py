from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.runtime_variant import (
    RuntimeVariantID,
)
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import GetSingleEntityOpsAction
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.repositories.runtime_variant.queriers import RuntimeVariantQuerier


@dataclass
class GetRuntimeVariantAction(GetSingleEntityOpsAction[RuntimeVariantRow, RuntimeVariantData]):
    """Read one runtime variant; every authenticated user may."""

    variant_id: RuntimeVariantID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "public_get_runtime_variant"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.variant_id

    @override
    def to_querier(self) -> RuntimeVariantQuerier:
        return RuntimeVariantQuerier(variant_id=self.variant_id)
