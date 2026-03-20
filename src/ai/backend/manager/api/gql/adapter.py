"""Base GraphQL adapter providing common utilities."""

from __future__ import annotations

from ai.backend.manager.api.adapters.pagination import (
    PaginationOptions as PaginationOptions,
)
from ai.backend.manager.api.adapters.pagination import (
    PaginationSpec as PaginationSpec,
)


class BaseGQLAdapter:
    """Base adapter providing common GraphQL query building utilities."""
