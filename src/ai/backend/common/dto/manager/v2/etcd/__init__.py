"""
Etcd DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.etcd.request import (
    DeleteConfigInput,
    GetConfigInput,
    GetResourceMetadataInput,
    SetConfigInput,
)
from ai.backend.common.dto.manager.v2.etcd.response import (
    AcceleratorMetadataNode,
    ConfigOkPayload,
    ConfigValuePayload,
    NumberFormatInfo,
    ResourceMetadataPayload,
    ResourceSlotNode,
    VfolderTypesPayload,
)

__all__ = (
    # Input models (request)
    "DeleteConfigInput",
    "GetConfigInput",
    "GetResourceMetadataInput",
    "SetConfigInput",
    # Node and Payload models (response)
    "AcceleratorMetadataNode",
    "ConfigOkPayload",
    "ConfigValuePayload",
    "NumberFormatInfo",
    "ResourceMetadataPayload",
    "ResourceSlotNode",
    "VfolderTypesPayload",
)
