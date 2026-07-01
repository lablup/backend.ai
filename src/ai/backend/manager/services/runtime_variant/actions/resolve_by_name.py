from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.identifier.runtime_variant import RuntimeVariantID
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.runtime_variant.actions.base import RuntimeVariantAction


@dataclass
class ResolveRuntimeVariantByNameAction(RuntimeVariantAction):
    """Resolve a runtime variant name into its ``RuntimeVariantID``.

    Used at the legacy API boundary (REST v1, gql_legacy) where clients
    still submit the variant by name; internal layers
    (adapter / service / sokovan) consume ``RuntimeVariantID`` only.
    """

    name: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def entity_id(self) -> str | None:
        return self.name


@dataclass
class ResolveRuntimeVariantByNameActionResult(BaseActionResult):
    runtime_variant_id: RuntimeVariantID

    @override
    def entity_id(self) -> str | None:
        return str(self.runtime_variant_id)
