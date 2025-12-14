"""Base types and utilities for repository layer.

Re-exports all public APIs for backward compatibility.
"""

from .creator import (
    Creator,
    CreatorResult,
    CreatorSpec,
    execute_creator,
)
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
from .updater import (
    Updater,
    UpdaterSpec,
)
from .upserter import (
    Upserter,
    UpserterResult,
    UpserterSpec,
    execute_upserter,
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
    # Creator
    "CreatorSpec",
    "Creator",
    "CreatorResult",
    "execute_creator",
    # Updater
    "UpdaterSpec",
    "Updater",
    # Upserter
    "UpserterSpec",
    "Upserter",
    "UpserterResult",
    "execute_upserter",
    # Purger
    "PurgeTarget",
    "Purger",
    "PurgerResult",
    "execute_purger",
    # Utils
    "combine_conditions_or",
    "negate_conditions",
]
