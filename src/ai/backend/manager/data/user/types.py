from __future__ import annotations

import enum
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Self, override
from uuid import UUID

from sqlalchemy.engine import Row

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.types import AccessKey
from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.data.permission.id import ScopeId
from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
    ScopeType,
)
from ai.backend.manager.errors.resource import DataTransformationFailed

if TYPE_CHECKING:
    from ai.backend.manager.models.user import UserRow
    from ai.backend.manager.repositories.base.creator import BulkCreatorError
    from ai.backend.manager.repositories.base.updater import BulkUpdaterError


class UserStatus(enum.StrEnum):
    """
    User account status.
    """

    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"
    BEFORE_VERIFICATION = "before-verification"

    @override
    @classmethod
    def _missing_(cls, value: Any) -> UserStatus | None:
        if not isinstance(value, str):
            raise DataTransformationFailed(
                f"UserStatus value must be a string, got {type(value).__name__}"
            )
        match value.upper():
            case "ACTIVE":
                return cls.ACTIVE
            case "INACTIVE":
                return cls.INACTIVE
            case "DELETED":
                return cls.DELETED
            case "BEFORE-VERIFICATION" | "BEFORE_VERIFICATION":
                return cls.BEFORE_VERIFICATION
        return None


@dataclass
class UserInfoContext:
    uuid: UUID
    email: str
    main_access_key: AccessKey


@dataclass
class UserData:
    id: UUID = field(compare=False)
    uuid: UUID = field(compare=False)  # legacy
    username: str | None
    email: str
    need_password_change: bool | None
    full_name: str | None
    description: str | None
    is_active: bool  # legacy
    status: str
    status_info: str | None
    created_at: datetime | None = field(compare=False)
    modified_at: datetime | None = field(compare=False)
    domain_name: str | None
    role: UserRole | None
    resource_policy: str
    allowed_client_ip: list[str] | None
    totp_activated: bool | None
    totp_activated_at: datetime | None = field(compare=False)
    sudo_session_enabled: bool
    main_access_key: str | None = field(compare=False)
    container_uid: int | None = field(compare=False)
    container_main_gid: int | None = field(compare=False)
    container_gids: list[int] | None = field(compare=False)

    def scope_id(self) -> ScopeId:
        return ScopeId(
            scope_type=ScopeType.USER,
            scope_id=str(self.id),
        )

    def role_name(self) -> str:
        return f"user-{str(self.id)[:8]}"

    def entity_operations(self) -> Mapping[EntityType, Iterable[OperationType]]:
        resource_entity_permissions = {
            entity: OperationType.owner_operations()
            for entity in EntityType.owner_accessible_entity_types_in_user()
        }
        user_permissions = OperationType.owner_operations() - {OperationType.CREATE}
        return {EntityType.USER: user_permissions, **resource_entity_permissions}

    @classmethod
    def from_row(cls, row: Row[Any]) -> Self:
        """
        Deprecated: Use `UserRow.to_data()` method instead.
        """
        return cls(
            id=row.uuid,
            uuid=row.uuid,
            username=row.username,
            email=row.email,
            need_password_change=row.need_password_change,
            full_name=row.full_name,
            description=row.description,
            is_active=row.status == UserStatus.ACTIVE,
            status=row.status,
            status_info=row.status_info,
            created_at=row.created_at,
            modified_at=row.modified_at,
            domain_name=row.domain_name,
            role=row.role,
            resource_policy=row.resource_policy,
            allowed_client_ip=row.allowed_client_ip,
            totp_activated=row.totp_activated,
            totp_activated_at=row.totp_activated_at,
            sudo_session_enabled=row.sudo_session_enabled,
            main_access_key=row.main_access_key,
            container_uid=row.container_uid,
            container_main_gid=row.container_main_gid,
            container_gids=row.container_gids,
        )


@dataclass
class UserCreateResultData:
    user: UserData
    keypair: KeyPairData


@dataclass
class UserSearchResult:
    """Result of user search operations."""

    items: list[UserData]
    """List of user data items."""

    total_count: int
    """Total number of items matching the query (before pagination)."""

    has_next_page: bool
    """Whether there are more items after the current page."""

    has_previous_page: bool
    """Whether there are items before the current page."""


@dataclass
class BulkUserCreateResultData:
    """Result of bulk user creation operation.

    Attributes:
        successes: Successfully created users
        failures: Failed user creation attempts with error info
    """

    successes: list[UserData] = field(default_factory=list)
    failures: list[BulkCreatorError[UserRow]] = field(default_factory=list)

    def success_count(self) -> int:
        """Get count of successfully created users."""
        return len(self.successes)

    def failure_count(self) -> int:
        """Get count of failed user creations."""
        return len(self.failures)


@dataclass
class BulkUserUpdateResultData:
    """Result of bulk user update operation.

    Attributes:
        successes: Successfully updated users
        failures: Failed user update attempts with error info
    """

    successes: list[UserData] = field(default_factory=list)
    failures: list[BulkUpdaterError[UserRow]] = field(default_factory=list)

    def success_count(self) -> int:
        """Get count of successfully updated users."""
        return len(self.successes)

    def failure_count(self) -> int:
        """Get count of failed user updates."""
        return len(self.failures)


@dataclass
class BulkPurgeError:
    """Error information for a failed bulk purge operation.

    Attributes:
        user_id: UUID of the user that failed to purge
        exception: The exception that occurred
    """

    user_id: UUID
    exception: Exception


@dataclass
class BulkUserPurgeResultData:
    """Result of bulk user purge operation.

    Attributes:
        purged_user_ids: UUIDs of successfully purged users
        failures: Failed user purge attempts with error info
    """

    purged_user_ids: list[UUID] = field(default_factory=list)
    failures: list[BulkPurgeError] = field(default_factory=list)

    def purged_count(self) -> int:
        """Get count of successfully purged users."""
        return len(self.purged_user_ids)

    def failure_count(self) -> int:
        """Get count of failed user purges."""
        return len(self.failures)
