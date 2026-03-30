"""
Common types for Resource Policy DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.types import DefaultForUnspecified

__all__ = (
    "DefaultForUnspecified",
    "KeypairResourcePolicyOrderField",
    "OrderDirection",
    "ProjectResourcePolicyOrderField",
    "UserResourcePolicyOrderField",
)


class KeypairResourcePolicyOrderField(StrEnum):
    """Fields available for ordering keypair resource policies."""

    NAME = "name"
    CREATED_AT = "created_at"
    MAX_SESSION_LIFETIME = "max_session_lifetime"
    MAX_CONCURRENT_SESSIONS = "max_concurrent_sessions"
    MAX_CONTAINERS_PER_SESSION = "max_containers_per_session"
    IDLE_TIMEOUT = "idle_timeout"
    MAX_CONCURRENT_SFTP_SESSIONS = "max_concurrent_sftp_sessions"
    MAX_PENDING_SESSION_COUNT = "max_pending_session_count"


class UserResourcePolicyOrderField(StrEnum):
    """Fields available for ordering user resource policies."""

    NAME = "name"
    CREATED_AT = "created_at"
    MAX_VFOLDER_COUNT = "max_vfolder_count"
    MAX_QUOTA_SCOPE_SIZE = "max_quota_scope_size"
    MAX_SESSION_COUNT_PER_MODEL_SESSION = "max_session_count_per_model_session"
    MAX_CUSTOMIZED_IMAGE_COUNT = "max_customized_image_count"


class ProjectResourcePolicyOrderField(StrEnum):
    """Fields available for ordering project resource policies."""

    NAME = "name"
    CREATED_AT = "created_at"
    MAX_VFOLDER_COUNT = "max_vfolder_count"
    MAX_QUOTA_SCOPE_SIZE = "max_quota_scope_size"
    MAX_NETWORK_COUNT = "max_network_count"
