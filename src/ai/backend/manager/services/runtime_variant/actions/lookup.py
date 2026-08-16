from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.runtime_variant import RUNTIME_VARIANT_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.actions.v2.ops.base import LookupEntityOpsAction
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.repositories.runtime_variant.lookups import RuntimeVariantLookup


@dataclass(frozen=True)
class RuntimeVariantNameKey(LookupKey):
    """The catalog name a caller passes instead of the variant's id."""

    name: str

    @override
    def kind(self) -> str:
        return "runtime_variant_name"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name}


@dataclass
class LookupRuntimeVariantAction(LookupEntityOpsAction[RuntimeVariantRow, RuntimeVariantData]):
    """Resolve a runtime variant name into the variant it names.

    Legacy API handlers call this before invoking id-typed internal adapters, so
    the adapter / service / sokovan chain never has to touch a name string.
    """

    name: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RUNTIME_VARIANT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_runtime_variant"

    @override
    def lookup_key(self) -> RuntimeVariantNameKey:
        return RuntimeVariantNameKey(name=self.name)

    @override
    def to_lookup(self) -> RuntimeVariantLookup:
        return RuntimeVariantLookup(name=self.name)
