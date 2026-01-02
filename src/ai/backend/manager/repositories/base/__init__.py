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
    BatchPurger,
    BatchPurgerResult,
    BatchPurgerSpec,
    Purger,
    PurgerResult,
    execute_batch_purger,
    execute_purger,
)
from .querier import (
    BatchQuerier,
    BatchQuerierResult,
    Querier,
    QuerierResult,
    execute_batch_querier,
    execute_querier,
)
from .types import (
    CursorConditionFactory,
    QueryCondition,
    QueryOrder,
)
from .updater import (
    BatchUpdater,
    BatchUpdaterResult,
    BatchUpdaterSpec,
    Updater,
    UpdaterResult,
    UpdaterSpec,
    execute_batch_updater,
    execute_updater,
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
    # BatchQuerier
    "BatchQuerier",
    "BatchQuerierResult",
    "execute_batch_querier",
    # Creator
    "CreatorSpec",
    "Creator",
    "CreatorResult",
    "execute_creator",
    # Updater
    "UpdaterSpec",
    "Updater",
    "UpdaterResult",
    "execute_updater",
    # BatchUpdater
    "BatchUpdaterSpec",
    "BatchUpdater",
    "BatchUpdaterResult",
    "execute_batch_updater",
    # Upserter
    "UpserterSpec",
    "Upserter",
    "UpserterResult",
    "execute_upserter",
    # Purger
    "Purger",
    "PurgerResult",
    "execute_purger",
    # BatchPurger
    "BatchPurgerSpec",
    "BatchPurger",
    "BatchPurgerResult",
    "execute_batch_purger",
    # Utils
    "combine_conditions_or",
    "negate_conditions",
]
