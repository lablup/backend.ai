from __future__ import annotations

from pydantic import Field

from ai.backend.common.identifier.deployment_preset import DeploymentPresetID
from ai.backend.common.types import BackendAISchema


class PresetValueEntry(BackendAISchema):
    preset_id: DeploymentPresetID = Field(description="Deployment preset ID.")
    value: str = Field(description="Value for this preset.")
