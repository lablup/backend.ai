from __future__ import annotations

import enum
from pathlib import Path
from typing import Literal
from uuid import UUID

from pydantic import ConfigDict, Field

from ai.backend.common.types import BackendAISchema


class ObjectType(enum.StrEnum):
    NONE = "NONE"
    ANY = "ANY"
    EVENT = "EVENT"
    MDS = "MDS"
    NODE = "NODE"
    FAN = "FAN"
    NIC = "NIC"
    HDD = "HDD"
    SSD = "SSD"
    DISK_DRIVE = "DISK_DRIVE"
    POWER_SUPPLY = "POWER_SUPPLY"
    DATA_SPHERE = "DATA_SPHERE"
    DATA_MOVER = "DATA_MOVER"
    DATA_PORTAL = "DATA_PORTAL"
    STORAGE_VOLUME = "STORAGE_VOLUME"
    VOLUME_GROUP = "VOLUME_GROUP"
    NETWORK_IF = "NETWORK_IF"
    MGMT = "MGMT"
    SHARE = "SHARE"
    BASE_USER = "BASE_USER"
    USER = "USER"
    FEDERATED_USER = "FEDERATED_USER"
    USER_GROUP = "USER_GROUP"
    IDENTITY_GROUP_MAPPING = "IDENTITY_GROUP_MAPPING"
    IDENTITY = "IDENTITY"
    MANAGEMENT_ROLE = "MANAGEMENT_ROLE"
    STEP = "STEP"
    TASK = "TASK"
    SMTP = "SMTP"
    NOTIFICATION_RULE = "NOTIFICATION_RULE"
    HEARTBEAT = "HEARTBEAT"
    NTP = "NTP"
    LOGICAL_VOLUME = "LOGICAL_VOLUME"
    LDAP = "LDAP"
    IDP = "IDP"
    DNS = "DNS"
    GATEWAY = "GATEWAY"
    DHCP = "DHCP"
    CLUSTER = "CLUSTER"
    CPU = "CPU"
    ELEMENTAL_OBJECTIVE = "ELEMENTAL_OBJECTIVE"
    OBJECTIVE = "OBJECTIVE"
    DATA_MANAGER = "DATA_MANAGER"
    SCHEDULE = "SCHEDULE"
    CONDITION = "CONDITION"
    SNAPSHOT_RETENTION = "SNAPSHOT_RETENTION"
    FILE_SNAPSHOT = "FILE_SNAPSHOT"
    OBJECT_STORE = "OBJECT_STORE"
    OBJECT_STORAGE_VOLUME = "OBJECT_STORAGE_VOLUME"
    CLOUD_MOVER = "CLOUD_MOVER"
    OBJECT_STORE_LOGICAL_VOLUME = "OBJECT_STORE_LOGICAL_VOLUME"
    NODE_LOCATION = "NODE_LOCATION"
    VOLUME_LOCATION = "VOLUME_LOCATION"
    SNMP = "SNMP"
    SW_UPDATE_TASK = "SW_UPDATE_TASK"
    CTDB = "CTDB"
    SHARE_SNAPSHOT = "SHARE_SNAPSHOT"
    BACKUP = "BACKUP"
    SAMBA_AD = "SAMBA_AD"
    DOMAIN_IDMAP = "DOMAIN_IDMAP"
    HMDB = "HMDB"
    SYSLOG = "SYSLOG"
    NIS = "NIS"
    NIS_CONFIG = "NIS_CONFIG"
    SUBNET_GATEWAY = "SUBNET_GATEWAY"
    STATIC_ROUTE = "STATIC_ROUTE"
    SITE = "SITE"
    SHARE_PARTICIPANT = "SHARE_PARTICIPANT"
    LOGIN_POLICY = "LOGIN_POLICY"
    DATA_COPY_TO_OBJECT_TASK = "DATA_COPY_TO_OBJECT_TASK"
    KMS = "KMS"
    BASE_STORAGE_VOLUME = "BASE_STORAGE_VOLUME"
    LICENSE_ACTIVATION = "LICENSE_ACTIVATION"
    SMB_ALIAS = "SMB_ALIAS"
    LOGICAL_SHARE = "LOGICAL_SHARE"
    WORM_ENTRY = "WORM_ENTRY"
    ANTIVIRUS = "ANTIVIRUS"
    ALCHEMI = "ALCHEMI"
    LABEL = "LABEL"
    S3_SERVER_CONFIG = "S3_SERVER_CONFIG"
    S3_SERVER_USER = "S3_SERVER_USER"
    S3_SERVER_BUCKET = "S3_SERVER_BUCKET"
    S3_SERVER_BUCKET_CONTAINER = "S3_SERVER_BUCKET_CONTAINER"


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


class ShareState(enum.StrEnum):
    OFFLINE = "OFFLINE"
    ONLINE = "ONLINE"
    MOUNTED = "MOUNTED"
    PUBLISHED = "PUBLISHED"
    CREATED = "CREATED"
    PRE_REMOVAL = "PRE_REMOVAL"
    REMOVING = "REMOVING"
    REMOVED = "REMOVED"
    RECLAIMING = "RECLAIMING"
    REMOVE_FAILED = "REMOVE_FAILED"


class ShareLifecycle(enum.StrEnum):
    CREATING = "CREATING"
    CREATED = "CREATED"
    PRE_DELETE = "PRE_DELETE"
    DELETE_SCHEDULED = "DELETE_SCHEDULED"
    DELETING = "DELETING"
    DELETE_FAILED = "DELETE_FAILED"


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


class SiteType(enum.StrEnum):
    LOCAL = "LOCAL"
    REMOTE = "REMOTE"


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

    def parse(self) -> ValidClusterMetricRow | None:
        if self.total is None or self.used is None or self.free is None:
            return None
        return ValidClusterMetricRow(
            time=self.time,
            total=self.total,
            used=self.used,
            free=self.free,
        )


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


class HammerspaceLoginRequest(BackendAISchema):
    username: str
    password: str


class HammerspaceCreateShareRequest(BackendAISchema):
    name: str
    path: str
    shareSizeLimit: int | None = None


class HammerspaceCreateShareQuery(BackendAISchema):
    model_config = ConfigDict(validate_by_name=True)

    create_path: Literal["true", "false"] = Field(alias="create-path")
    validate_only: Literal["true", "false"] = Field(alias="validate-only")


class HammerspaceGetShareQuery(BackendAISchema):
    spec: str


class HammerspaceGetObjectiveQuery(BackendAISchema):
    spec: str


class HammerspaceClusterMetricQuery(BackendAISchema):
    precedingDuration: str
    intervalDuration: str


class CreateShareParams(BackendAISchema):
    name: str
    path: Path
    share_size_limit: int | None = None
    create_path: bool = True
    validate_only: bool = False

    def query(self) -> HammerspaceCreateShareQuery:
        return HammerspaceCreateShareQuery(
            create_path="true" if self.create_path else "false",
            validate_only="true" if self.validate_only else "false",
        )

    def body(self) -> HammerspaceCreateShareRequest:
        return HammerspaceCreateShareRequest(
            name=self.name,
            path=str(self.path),
            shareSizeLimit=self.share_size_limit,
        )


class GetShareParams(BackendAISchema):
    name: str

    def query(self) -> HammerspaceGetShareQuery:
        return HammerspaceGetShareQuery(spec=f"name=eq={self.name}")


class ClusterMetricParams(BackendAISchema):
    site_id: UUID
    preceding_duration: str  # "7d", "24h", "60m"
    interval_duration: str  # "1d", "1h", "5m"
    object_type: ObjectType = ObjectType.CLUSTER

    def query(self) -> HammerspaceClusterMetricQuery:
        return HammerspaceClusterMetricQuery(
            precedingDuration=self.preceding_duration,
            intervalDuration=self.interval_duration,
        )
