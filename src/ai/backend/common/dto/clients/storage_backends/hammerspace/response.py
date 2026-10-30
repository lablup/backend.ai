from __future__ import annotations

from uuid import UUID

from pydantic import ConfigDict

from ai.backend.common.dto.clients.storage_backends.hammerspace.types import (
    ObjectType,
    Priority,
    ShareLifecycle,
    ShareState,
    SiteType,
)
from ai.backend.common.types import BackendAISchema


class UOID(BackendAISchema):
    uuid: UUID
    objectType: ObjectType


class DFEntry(BackendAISchema):
    total: int
    used: int
    available: int
    percent: int


class Location(BackendAISchema):
    model_config = ConfigDict(extra="allow")

    uoid: UOID
    modified: int  # timestamp
    excludeFromObjectiveUuid: UUID
    confineToObjectiveUuid: UUID
    placeOnObjectiveUuid: UUID


class LocationList(BackendAISchema):
    id: int
    placeOn: list[Location]


class PlacementObjective(BackendAISchema):
    model_config = ConfigDict(extra="allow")

    id: int
    excludeFrom: list[Location]  # Locations never to place data
    confineTo: list[Location]  # Locations to only place data on
    placeOnLocations: list[LocationList]  # Preferred locations to place data on


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


class ShareObjective(BackendAISchema):
    model_config = ConfigDict(extra="allow")

    objective: SimpleObjective
    applicability: str
    removable: bool


class SimpleShare(BackendAISchema):
    model_config = ConfigDict(extra="allow")

    uoid: UOID
    name: str
    path: str


class Share(BackendAISchema):
    model_config = ConfigDict(extra="allow")

    uoid: UOID
    name: str
    modified: int  # timestamp
    totalNumberOfFiles: int
    inodes: DFEntry
    space: DFEntry
    path: str
    shareState: ShareState
    shareLifecycle: ShareLifecycle
    shareObjectives: list[ShareObjective]


class Site(BackendAISchema):
    model_config = ConfigDict(extra="allow")

    uoid: UOID
    created: int  # timestamp
    modified: int  # timestamp
    name: str
    type: SiteType


class ClusterMetricRow(BackendAISchema):
    model_config = ConfigDict(extra="allow")

    time: int  # timestamp
    total: int | None
    used: int | None
    free: int | None


class ValidClusterMetricRow(BackendAISchema):
    time: int  # timestamp
    total: int
    used: int
    free: int


class MetricSeries(BackendAISchema):
    model_config = ConfigDict(extra="allow")

    tags: dict[str, str]
    rows: list[ClusterMetricRow]


class Metric(BackendAISchema):
    model_config = ConfigDict(extra="allow")

    series: list[MetricSeries]
