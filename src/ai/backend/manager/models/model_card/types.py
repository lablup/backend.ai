from __future__ import annotations

from pydantic import BaseModel, Field


class MinResourceSpec(BaseModel):
    slots: dict[str, str] = Field(default_factory=dict)
