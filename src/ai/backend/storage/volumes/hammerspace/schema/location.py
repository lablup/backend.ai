import uuid

from pydantic import BaseModel, ConfigDict

from .uoid import UOID


class Location(BaseModel):
    model_config = ConfigDict(extra="allow")

    uoid: UOID
    modified: int  # timestamp
    excludeFromObjectiveUuid: uuid.UUID
    confineToObjectiveUuid: uuid.UUID
    placeOnObjectiveUuid: uuid.UUID


class LocationList(BaseModel):
    id: int
    placeOn: list[Location]
