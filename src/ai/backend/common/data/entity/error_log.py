from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "ERROR_LOG_ENTITY_TYPE",
    "ErrorLogID",
)


# Raw string mirroring the RBAC-managed EntityType.ERROR_LOG value.
ERROR_LOG_ENTITY_TYPE = EntityType("error_log")


class ErrorLogID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ERROR_LOG_ENTITY_TYPE
