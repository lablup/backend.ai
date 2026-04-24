from __future__ import annotations

from pydantic import BaseModel, Field

from ai.backend.common.identifier.deployment_preset import DeploymentPresetID


class PresetValueEntry(BaseModel):
    preset_id: DeploymentPresetID = Field(description="Deployment preset ID.")
    value: str = Field(description="Value for this preset.")
