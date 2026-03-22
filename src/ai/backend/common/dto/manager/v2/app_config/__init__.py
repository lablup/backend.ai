"""
App configuration DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.app_config.request import (
    DeleteDomainConfigInput,
    DeleteUserConfigInput,
    UpsertDomainConfigInput,
    UpsertUserConfigInput,
)
from ai.backend.common.dto.manager.v2.app_config.response import (
    AppConfigNode,
    DeleteDomainConfigPayload,
    DeleteUserConfigPayload,
    UpsertDomainConfigPayloadDTO,
    UpsertUserConfigPayloadDTO,
)

__all__ = (
    "DeleteDomainConfigInput",
    "DeleteUserConfigInput",
    "UpsertDomainConfigInput",
    "UpsertUserConfigInput",
    "AppConfigNode",
    "DeleteDomainConfigPayload",
    "DeleteUserConfigPayload",
    "UpsertDomainConfigPayloadDTO",
    "UpsertUserConfigPayloadDTO",
)
