import enum
from typing import Optional

from pydantic import BaseModel, ConfigDict

from .placement_objective import PlacementObjective
from .uoid import UOID


class Priority(enum.StrEnum):
    LOW = "LOW"
    MEDIUM_LOW = "MEDIUM_LOW"
    MEDIUM = "MEDIUM"
    MEDIUM_HIGH = "MEDIUM_HIGH"
    HIGH = "HIGH"


class SimpleObjective(BaseModel):
    model_config = ConfigDict(extra="allow")

    uoid: UOID
    name: str
    zombie: bool
    hidden: bool
    internalId: int


class AppliedObjective(BaseModel):
    applicability: str
    id: int


class Objective(BaseModel):
    model_config = ConfigDict(extra="allow")

    uoid: UOID
    name: str
    modified: int  # timestamp
    priority: Priority
    appliedObjectives: list[AppliedObjective]
    basic: bool
    internalId: int
    hidden: bool
    placementObjective: Optional[PlacementObjective] = None
