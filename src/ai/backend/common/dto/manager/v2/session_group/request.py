"""
Request DTOs for SessionGroup v2 API.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from typing import Self
from uuid import UUID

from pydantic import Field, model_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import (
    DateTimeFilter,
    EnumFilter,
    NullableDateTimeFilter,
    UUIDFilter,
)
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.session_group.types import (
    SessionGroupAdmissionEnum,
    SessionGroupOrderField,
    SessionGroupPlacementDirectionEnum,
    SessionGroupPlacementEnforcementEnum,
    SessionGroupScope,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.common.tristate.unset import UNSET, Unset

MIN_MEMBER_COUNT = 2
"""The smallest member count an `all_or_none` group takes."""

__all__ = (
    "AdminSearchSessionGroupsInput",
    "CreateSessionGroupInput",
    "PurgeSessionGroupInput",
    "ScopedSearchSessionGroupsInput",
    "SessionGroupFilter",
    "SessionGroupOrder",
    "SessionGroupPlacementDirectionFilter",
    "SessionGroupPlacementEnforcementFilter",
    "UpdateSessionGroupInput",
)


class SessionGroupPlacementDirectionFilter(EnumFilter[SessionGroupPlacementDirectionEnum]):
    """Filter for the placement direction of a session group."""


class SessionGroupPlacementEnforcementFilter(EnumFilter[SessionGroupPlacementEnforcementEnum]):
    """Filter for the placement enforcement of a session group."""


class SessionGroupFilter(BaseRequestModel):
    """Filter for session groups.

    Groups marked deleted are left out unless the top-level filter gives ``deleted_at``.
    A ``deleted_at`` inside ``AND``/``OR``/``NOT`` does not lift that default.
    """

    entity_id: UUIDFilter | None = Field(default=None, description="Filter by session group ID.")
    domain_id: UUIDFilter | None = Field(default=None, description="Filter by domain ID.")
    project_id: UUIDFilter | None = Field(default=None, description="Filter by project ID.")
    owner_user_id: UUIDFilter | None = Field(
        default=None, description="Filter by the ID of the owning user."
    )
    placement_direction: SessionGroupPlacementDirectionFilter | None = Field(
        default=None, description="Filter by placement direction."
    )
    placement_enforcement: SessionGroupPlacementEnforcementFilter | None = Field(
        default=None, description="Filter by placement enforcement."
    )
    created_at: DateTimeFilter | None = Field(default=None, description="Filter by creation time.")
    deleted_at: NullableDateTimeFilter | None = Field(
        default=None,
        description=(
            "Filter by deletion time. Setting it on the top-level filter includes the groups "
            "marked deleted; inside AND, OR or NOT it does not."
        ),
    )

    AND: list[SessionGroupFilter] | None = Field(
        default=None, description="AND logical combinator."
    )
    OR: list[SessionGroupFilter] | None = Field(default=None, description="OR logical combinator.")
    NOT: list[SessionGroupFilter] | None = Field(
        default=None, description="NOT logical combinator."
    )


SessionGroupFilter.model_rebuild()


class SessionGroupOrder(BaseRequestModel):
    """Order specification for session groups."""

    field: SessionGroupOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction.")


class ScopedSearchSessionGroupsInput(BaseRequestModel):
    """Input for searching session groups within scopes."""

    scope: SessionGroupScope = Field(description="Scope (OR across all items).")
    filter: SessionGroupFilter | None = Field(default=None, description="Filter conditions.")
    order: list[SessionGroupOrder] | None = Field(default=None, description="Order specifications.")
    first: int | None = Field(default=None, description="Cursor pagination: number of items.")
    after: str | None = Field(default=None, description="Cursor pagination: after cursor.")
    last: int | None = Field(default=None, description="Cursor pagination: last N items.")
    before: str | None = Field(default=None, description="Cursor pagination: before cursor.")
    limit: int | None = Field(default=None, description="Offset pagination: maximum items.")
    offset: int | None = Field(default=None, description="Offset pagination: number to skip.")


class AdminSearchSessionGroupsInput(BaseRequestModel):
    """Input for searching every session group (superadmin)."""

    filter: SessionGroupFilter | None = Field(default=None, description="Filter conditions.")
    order: list[SessionGroupOrder] | None = Field(default=None, description="Order specifications.")
    first: int | None = Field(default=None, description="Cursor pagination: number of items.")
    after: str | None = Field(default=None, description="Cursor pagination: after cursor.")
    last: int | None = Field(default=None, description="Cursor pagination: last N items.")
    before: str | None = Field(default=None, description="Cursor pagination: before cursor.")
    limit: int | None = Field(default=None, description="Offset pagination: maximum items.")
    offset: int | None = Field(default=None, description="Offset pagination: number to skip.")


class PurgeSessionGroupInput(BaseRequestModel):
    """Input for removing a session group; its member sessions stay with their group cleared."""

    id: UUID = Field(description="ID of the session group to purge.")


class UpdateSessionGroupInput(BaseRequestModel):
    """Input for changing a session group's placement policy and admission.

    At least one field must be given. The admission and the member count do not change
    while a member is pending.
    """

    id: UUID = Field(description="ID of the session group to update.")
    placement_direction: SessionGroupPlacementDirectionEnum | None | Unset = Field(
        default=UNSET,
        description="New placement direction. Omit to leave unchanged.",
    )
    placement_enforcement: SessionGroupPlacementEnforcementEnum | None | Unset = Field(
        default=UNSET,
        description="New placement enforcement. Omit to leave unchanged.",
    )
    admission: SessionGroupAdmissionEnum | None | Unset = Field(
        default=UNSET,
        description=(
            f"Added in {NEXT_RELEASE_VERSION}. New admission. Omit to leave unchanged;"
            " `independent` without `member_count` clears the member count."
        ),
    )
    member_count: int | None | Unset = Field(
        default=UNSET,
        description=(
            f"Added in {NEXT_RELEASE_VERSION}. New member count of an `all_or_none` group,"
            " at least 2. Null clears it. Omit to leave unchanged."
        ),
    )

    @model_validator(mode="after")
    def _require_a_change(self) -> Self:
        given = (
            isinstance(self.placement_direction, SessionGroupPlacementDirectionEnum),
            isinstance(self.placement_enforcement, SessionGroupPlacementEnforcementEnum),
            isinstance(self.admission, SessionGroupAdmissionEnum),
            not isinstance(self.member_count, Unset),
        )
        if isinstance(self.member_count, int) and self.member_count < MIN_MEMBER_COUNT:
            raise ValueError(f"'member_count' must be at least {MIN_MEMBER_COUNT}")
        if not any(given):
            raise ValueError(
                "UpdateSessionGroupInput requires 'placement_direction', 'placement_enforcement',"
                " 'admission' or 'member_count'"
            )
        return self


class CreateSessionGroupInput(BaseRequestModel):
    """Input for creating a session group in a project; the caller becomes its owner."""

    project_id: UUID = Field(description="ID of the project the session group is created in.")
    placement_direction: SessionGroupPlacementDirectionEnum = Field(
        description="How the member sessions sit relative to each other, per agent.",
    )
    placement_enforcement: SessionGroupPlacementEnforcementEnum = Field(
        description="How hard the placement direction is enforced.",
    )
    admission: SessionGroupAdmissionEnum = Field(
        default=SessionGroupAdmissionEnum.INDEPENDENT,
        description=(
            f"Added in {NEXT_RELEASE_VERSION}. Whether the members are admitted one by one"
            " (`independent`) or all at once (`all_or_none`)."
        ),
    )
    member_count: int | None = Field(
        default=None,
        ge=MIN_MEMBER_COUNT,
        description=(
            f"Added in {NEXT_RELEASE_VERSION}. Members an `all_or_none` group admits together;"
            " required for `all_or_none`, empty for `independent`."
        ),
    )

    @model_validator(mode="after")
    def _match_member_count(self) -> Self:
        if self.admission == SessionGroupAdmissionEnum.ALL_OR_NONE and self.member_count is None:
            raise ValueError("An all_or_none session group requires 'member_count'")
        if (
            self.admission == SessionGroupAdmissionEnum.INDEPENDENT
            and self.member_count is not None
        ):
            raise ValueError("An independent session group takes no 'member_count'")
        return self
