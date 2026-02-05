"""Base types and utilities for repository layer.

Re-exports all public APIs for backward compatibility.
"""

from .creator import (
    BulkCreator,
    BulkCreatorError,
    BulkCreatorResult,
    BulkCreatorResultWithFailures,
    Creator,
    CreatorResult,
    CreatorSpec,
    execute_bulk_creator,
    execute_bulk_creator_partial,
    execute_creator,
)
from .export import (
    ExportDataStream,
    ExportFieldDef,
    ExportFieldType,
    ExportFormatter,
    ExportLimitExceeded,
    ExportQueryParams,
    ReportDef,
    StreamingExportQuery,
    execute_streaming_export,
)
from .pagination import (
    CursorBackwardPagination,
    CursorForwardPagination,
    NoPagination,
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
    ExistenceCheck,
    QueryCondition,
    QueryOrder,
    SearchScope,
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
    BulkUpserter,
    BulkUpserterResult,
    Upserter,
    UpserterResult,
    UpserterSpec,
    execute_bulk_upserter,
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
    "ExistenceCheck",
    "SearchScope",
    # Export
    "ExportDataStream",
    "ExportFieldDef",
    "ExportFieldType",
    "ExportFormatter",
    "ExportLimitExceeded",
    "ExportQueryParams",
    "ReportDef",
    "StreamingExportQuery",
    "execute_streaming_export",
    # Pagination
    "QueryPagination",
    "NoPagination",
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
    # BulkCreator
    "BulkCreator",
    "BulkCreatorError",
    "BulkCreatorResult",
    "BulkCreatorResultWithFailures",
    "execute_bulk_creator",
    "execute_bulk_creator_partial",
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
    # BulkUpserter
    "BulkUpserter",
    "BulkUpserterResult",
    "execute_bulk_upserter",
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
