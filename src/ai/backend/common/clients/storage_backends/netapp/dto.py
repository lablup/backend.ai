from __future__ import annotations

import enum
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any
from uuid import UUID

from pydantic import ConfigDict, Field, PlainSerializer

from ai.backend.common.types import BackendAISchema

CommaSeparatedFields = Annotated[
    list[str], PlainSerializer(lambda fields: ",".join(fields), return_type=str)
]


class NetAppJobResponseCode(enum.StrEnum):
    QUOTA_ALEADY_ENABLED = "5308507"


class NetAppJobResult(BackendAISchema):
    state: str
    code: str | None
    message: str | None


class NetAppSpaceInfo(BackendAISchema):
    model_config = ConfigDict(extra="allow")

    size: int
    used: int
    available: int | None = None


class NetAppSVMInfo(BackendAISchema):
    model_config = ConfigDict(extra="allow")

    uuid: str
    name: str


class NetAppVolumeInfo(BackendAISchema):
    model_config = ConfigDict(extra="allow")

    name: str
    uuid: UUID
    path: Path
    space: NetAppSpaceInfo | None = None
    statistics: dict[str, Any] | None = None
    svm: NetAppSVMInfo | None = None


class NetAppVolumeMetric(BackendAISchema):
    model_config = ConfigDict(extra="allow")


class NetAppQTreeInfo(BackendAISchema):
    model_config = ConfigDict(extra="allow")

    id: int
    name: str
    path: Path
    security_style: str | None = None
    export_policy: dict[str, Any] | None = None
    statistics: dict[str, Any] | None = None


class NetAppQuotaConfig(BackendAISchema):
    limit_bytes: int


class NetAppQuotaUsage(BackendAISchema):
    used_bytes: int
    limit_bytes: int


class NetAppQoSFixedPolicy(BackendAISchema):
    max_throughput_iops: int
    max_throughput_mbps: int
    min_throughput_iops: int
    min_throughput_mbps: int
    capacity_shared: bool


class NetAppQoSPolicy(BackendAISchema):
    uuid: str
    name: str
    fixed: NetAppQoSFixedPolicy
    svm: NetAppSVMInfo


class NetAppVolumeQoS(BackendAISchema):
    model_config = ConfigDict(extra="allow")


class NetAppCluster(BackendAISchema):
    cluster_name: str
    cluster_uuid: str
    version: str


class NetAppXCPEntryType(enum.Enum):
    FILE = 0
    DIRECTORY = 1
    SYMLINK = 2


class NetAppXCPStat(BackendAISchema):
    size: int
    owner: str
    mode: int
    modified: datetime
    created: datetime


class NetAppXCPEntry(BackendAISchema):
    name: str
    path: Path
    type: NetAppXCPEntryType
    stat: NetAppXCPStat
    symlink_target: str


class NetAppXCPTreeUsage(BackendAISchema):
    file_count: int
    used_bytes: int


class NetAppCreateQTreeRequest(BackendAISchema):
    model_config = ConfigDict(populate_by_name=True)

    svm_uuid: UUID = Field(alias="svm.uuid")
    volume_uuid: UUID = Field(alias="volume.uuid")
    name: str
    user_id: int = Field(alias="user.id")
    group_id: int = Field(alias="group.id")


class NetAppQuotaSpaceLimit(BackendAISchema):
    hard_limit: int
    soft_limit: int


class NetAppCreateQuotaRuleRequest(BackendAISchema):
    model_config = ConfigDict(populate_by_name=True)

    svm_uuid: UUID = Field(alias="svm.uuid")
    volume_uuid: UUID = Field(alias="volume.uuid")
    type: str = "tree"
    qtree_name: str = Field(alias="qtree.name")
    space: NetAppQuotaSpaceLimit


class NetAppUpdateQuotaRuleRequest(BackendAISchema):
    space: NetAppQuotaSpaceLimit


class NetAppEnableQuotaRequest(BackendAISchema):
    model_config = ConfigDict(populate_by_name=True)

    quota_enabled: bool = Field(alias="quota.enabled")


class NetAppVolumeListQuery(BackendAISchema):
    fields: CommaSeparatedFields


class NetAppVolumeByNameQuery(BackendAISchema):
    name: str
    fields: CommaSeparatedFields


class NetAppVolumeQuery(BackendAISchema):
    fields: CommaSeparatedFields


class NetAppVolumeMetricQuery(BackendAISchema):
    fields: CommaSeparatedFields


class NetAppQTreeListQuery(BackendAISchema):
    fields: CommaSeparatedFields


class NetAppQTreeQuery(BackendAISchema):
    fields: CommaSeparatedFields


class NetAppQTreeByNameQuery(BackendAISchema):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    volume_uuid: UUID = Field(alias="volume.uuid")
    fields: CommaSeparatedFields


class NetAppQuotaRuleQuery(BackendAISchema):
    model_config = ConfigDict(populate_by_name=True)

    svm_uuid: UUID = Field(alias="svm.uuid")
    volume_uuid: UUID = Field(alias="volume.uuid")
    type: str = "tree"
    qtree_name: str = Field(alias="qtree.name")
    fields: str = "space,files"


class NetAppQuotaReportQuery(BackendAISchema):
    model_config = ConfigDict(populate_by_name=True)

    type: str = "tree"
    svm_uuid: UUID = Field(alias="svm.uuid")
    volume_uuid: UUID = Field(alias="volume.uuid")
    qtree_name: str = Field(alias="qtree.name")
    fields: str = "space"


class NetAppVolumeQoSQuery(BackendAISchema):
    fields: str = "qos"
