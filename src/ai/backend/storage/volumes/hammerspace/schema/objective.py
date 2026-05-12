import enum

from pydantic import ConfigDict

from ai.backend.common.types import BackendAISchema

from .placement_objective import PlacementObjective
from .uoid import UOID


class Priority(enum.StrEnum):
    LOW = "LOW"
    MEDIUM_LOW = "MEDIUM_LOW"
    MEDIUM = "MEDIUM"
    MEDIUM_HIGH = "MEDIUM_HIGH"
    HIGH = "HIGH"


class SimpleObjective(BackendAISchema):
    model_config = ConfigDict(extra="allow")

    uoid: UOID
    name: str
    zombie: bool
    hidden: bool
    internalId: int


class AppliedObjective(BackendAISchema):
    applicability: str
    id: int


class Objective(BackendAISchema):
    model_config = ConfigDict(extra="allow")

    uoid: UOID
    name: str
    modified: int  # timestamp
    priority: Priority
    appliedObjectives: list[AppliedObjective]
    basic: bool
    internalId: int
    hidden: bool
    placementObjective: PlacementObjective | None = None
