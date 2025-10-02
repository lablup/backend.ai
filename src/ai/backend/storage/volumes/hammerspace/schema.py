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


class Capacity(BaseModel):
    total: int
    used: int
    free: int


class IPAddress(BaseModel):
    address: str
    prefixLength: int


class QualifiedAddress(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: UOID
    ip: IPAddress
    port: int
    netId: str
    nodeNum: int
    stripeClass: int
    failoverClass: int


class LogicalVolume(BaseModel):
    model_config = ConfigDict(extra="allow")

    uoid: UOID
    name: str
    serviceState: str
    addresses: list[QualifiedAddress]
    exportPath: str
    aliases: list[str]
    fsType: str
    capacity: Capacity


class StorageVolume(BaseModel):
    model_config = ConfigDict(extra="allow")

    uoid: UOID
    name: str
    logicalVolume: LogicalVolume
    storageVolumeState: str
    uri: str


class Objective(BaseModel):
    model_config = ConfigDict(extra="allow")

    uoid: UOID
    name: str
    placementObjective: PlacementObjective
