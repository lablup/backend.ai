from pydantic import ConfigDict

from ai.backend.common.types import BackendAISchema

from .location import Location, LocationList


class PlacementObjective(BackendAISchema):
    model_config = ConfigDict(extra="allow")

    id: int
    excludeFrom: list[Location]  # Locations never to place data
    confineTo: list[Location]  # Locations to only place data on
    placeOnLocations: list[LocationList]  # Preferred locations to place data on
