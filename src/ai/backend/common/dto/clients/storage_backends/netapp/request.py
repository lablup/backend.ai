from __future__ import annotations

from uuid import UUID

from pydantic import ConfigDict, Field

from ai.backend.common.dto.clients.storage_backends.netapp.response import (
    NetAppQuotaSpaceLimit,
)
from ai.backend.common.dto.clients.storage_backends.netapp.types import (
    CommaSeparatedFields,
)
from ai.backend.common.types import BackendAISchema


class NetAppCreateQTreeRequest(BackendAISchema):
    model_config = ConfigDict(populate_by_name=True)

    svm_uuid: UUID = Field(alias="svm.uuid")
    volume_uuid: UUID = Field(alias="volume.uuid")
    name: str
    user_id: int = Field(alias="user.id")
    group_id: int = Field(alias="group.id")


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

    quota_enabled: bool = Field(default=True, alias="quota.enabled")


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
