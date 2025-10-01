from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict


@dataclass
class CreateShareParams:
    name: str
    path: str
    create_path: bool = True
    validate_only: bool = False

    def query(self) -> dict[str, str]:
        return {
            "create-path": "true" if self.create_path else "false",
            "validate-only": "true" if self.validate_only else "false",
        }

    def body(self) -> dict[str, str]:
        return {
            "name": self.name,
            "path": self.path,
        }


class Share(BaseModel):
    model_config = ConfigDict(extra="allow")

    uoid: UOID
    name: str


class UOID(BaseModel):
    uuid: str
    objectType: str


class Location(BaseModel):
    model_config = ConfigDict(extra="allow")

    uoid: UOID
    placeOnObjectiveUuid: str
    excludeFromObjectiveUuid: str
    confineToObjectiveUuid: str


class LocationList(BaseModel):
    id: int
    placeOn: list[Location]


class PlacementObjective(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    placeOnLocations: list[LocationList]
    excludeFrom: list[Location]
    confineTo: list[Location]
    allowedOnlineDelay: int
    doNotMove: bool
    capacityOptimize: bool


class Objective(BaseModel):
    model_config = ConfigDict(extra="allow")

    uoid: UOID
    name: str
    placementObjective: PlacementObjective
