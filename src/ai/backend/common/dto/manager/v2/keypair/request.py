"""
Request DTOs for keypair DTO v2.
"""

from __future__ import annotations

from typing import Self

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import DateTimeFilter, StringFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.keypair.types import KeypairOrderField

__all__ = (
    "KeypairFilter",
    "KeypairOrderBy",
    "SearchMyKeypairsGQLInput",
)


class KeypairFilter(BaseRequestModel):
    """Filter for keypair search."""

    is_active: bool | None = None
    is_admin: bool | None = None
    access_key: StringFilter | None = None
    resource_policy: StringFilter | None = None
    created_at: DateTimeFilter | None = None
    last_used: DateTimeFilter | None = None

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


KeypairFilter.model_rebuild()


class KeypairOrderBy(BaseRequestModel):
    """Order by specification for keypairs."""

    field: KeypairOrderField
    direction: OrderDirection = OrderDirection.DESC


class SearchMyKeypairsGQLInput(BaseRequestModel):
    """GQL pagination search input for current user's keypairs."""

    filter: KeypairFilter | None = None
    order: list[KeypairOrderBy] | None = None
    first: int | None = None
    after: str | None = None
    last: int | None = None
    before: str | None = None
    limit: int | None = None
    offset: int | None = None
