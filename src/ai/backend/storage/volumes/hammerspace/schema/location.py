import uuid

from pydantic import ConfigDict

from ai.backend.common.types import BackendAISchema

from .uoid import UOID


class Location(BackendAISchema):
    model_config = ConfigDict(extra="allow")

    uoid: UOID
    modified: int  # timestamp
    excludeFromObjectiveUuid: uuid.UUID
    confineToObjectiveUuid: uuid.UUID
    placeOnObjectiveUuid: uuid.UUID


class LocationList(BackendAISchema):
    id: int
    placeOn: list[Location]
