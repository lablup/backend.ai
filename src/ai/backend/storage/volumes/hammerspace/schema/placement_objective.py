from pydantic import BaseModel, ConfigDict

from .location import Location, LocationList


class PlacementObjective(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    excludeFrom: list[Location]  # Locations never to place data
    confineTo: list[Location]  # Locations to only place data on
    placeOnLocations: list[LocationList]  # Preferred locations to place data on
