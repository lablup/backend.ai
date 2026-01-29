"""GraphQL info sub-types for Role following BEP-1038 pattern."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import strawberry

from .enums import RoleSourceGQL, RoleStatusGQL


@strawberry.type(
    name="RoleIdentityInfo",
    description="Added in 26.2.0. Identity information for a role",
)
class RoleIdentityInfo:
    name: str
    description: Optional[str]
    source: RoleSourceGQL


@strawberry.type(
    name="RoleLifecycleInfo",
    description="Added in 26.2.0. Lifecycle information for a role",
)
class RoleLifecycleInfo:
    status: RoleStatusGQL
    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]
