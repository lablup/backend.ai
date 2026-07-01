from __future__ import annotations

from pydantic import Field

from ai.backend.common.identifier.runtime_variant_preset import RuntimeVariantPresetID
from ai.backend.common.types import BackendAISchema


class RuntimeVariantPresetValueEntry(BackendAISchema):
    """A concrete value bound to a runtime variant preset, stored as JSONB."""

    preset_id: RuntimeVariantPresetID = Field(description="Runtime variant preset ID.")
    value: str = Field(description="Value for this preset.")
