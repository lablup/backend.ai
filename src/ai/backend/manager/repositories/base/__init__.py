"""Base types and utilities for repository layer.

Re-exports all public APIs for backward compatibility.
"""

from .pagination import (
    CursorBackwardPagination,
    CursorForwardPagination,
    OffsetPagination,
    PageInfoResult,
    QueryPagination,
)
from .purger import (
    Purger,
    PurgerResult,
    PurgeTarget,
    execute_purger,
)
from .querier import (
    Querier,
    QuerierResult,
    execute_querier,
)
from .types import (
    CursorConditionFactory,
    QueryCondition,
    QueryOrder,
)
from .utils import (
    combine_conditions_or,
    negate_conditions,
)

__all__ = [
    # Types
    "QueryCondition",
    "QueryOrder",
    "CursorConditionFactory",
    # Pagination
    "QueryPagination",
    "OffsetPagination",
    "CursorForwardPagination",
    "CursorBackwardPagination",
    "PageInfoResult",
    # Querier
    "Querier",
    "QuerierResult",
    "execute_querier",
    # Purger
    "PurgeTarget",
    "Purger",
    "PurgerResult",
    "execute_purger",
    # Utils
    "combine_conditions_or",
    "negate_conditions",
]
