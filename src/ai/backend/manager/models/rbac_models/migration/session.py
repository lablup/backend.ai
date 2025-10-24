from collections.abc import Mapping

from .enums import (
    OperationType,
    RoleSource,
)

role_source_to_operation: Mapping[RoleSource, set[OperationType]] = {
    RoleSource.SYSTEM: OperationType.owner_operations(),
    RoleSource.CUSTOM: OperationType.member_operations(),
}
