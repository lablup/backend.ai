from typing import NewType
from uuid import UUID

from ai.backend.common.data.entity.types import EntityType

__all__ = (
    "ERROR_LOG_ENTITY_TYPE",
    "ErrorLogID",
)


# Raw string mirroring the RBAC-managed EntityType.ERROR_LOG value.
ERROR_LOG_ENTITY_TYPE = EntityType("error_log")

ErrorLogID = NewType("ErrorLogID", UUID)
