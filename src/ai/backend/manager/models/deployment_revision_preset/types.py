from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class PresetValueEntry(BaseModel):
    preset_id: UUID = Field(description="Runtime variant preset ID.")
    value: str = Field(description="Value for this preset.")
