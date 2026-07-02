"""Base types and utilities for repository layer.

Re-exports all public APIs for backward compatibility.
"""

from .creator import (
    BulkConditionalCreator,
    BulkCreator,
    BulkCreatorError,
    BulkCreatorResult,
    BulkCreatorResultWithFailures,
    ConditionalCreator,
    Creator,
    CreatorResult,
    CreatorSpec,
    DependentCreatorSpec,
    NextValuePolicy,
    execute_bulk_creator,
    execute_bulk_creator_partial,
    execute_bulk_dependent_creator,
    execute_creator,
    execute_dependent_creator,
    execute_next_value_creator,
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
from .integrity import (
    match_integrity_error,
    parse_integrity_error,
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
    BulkConditionalPurger,
    BulkPurgerError,
    BulkPurgerResultWithFailures,
    ConditionalPurger,
    Purger,
    PurgerResult,
    execute_batch_purger,
    execute_bulk_purger_partial,
    execute_purger,
)
from .querier import (
    BatchQuerier,
    BatchQuerierResult,
    ExistsQuerier,
    Querier,
    QuerierResult,
    execute_batch_querier,
    execute_querier,
)
from .types import (
    CursorConditionFactory,
    IntegrityErrorCheck,
)
from .updater import (
    BatchUpdater,
    BatchUpdaterResult,
    BatchUpdaterSpec,
    BulkConditionalUpdater,
    BulkUpdaterError,
    BulkUpdaterResult,
    ConditionalUpdater,
    Updater,
    UpdaterResult,
    UpdaterSpec,
    execute_batch_updater,
    execute_bulk_updater_partial,
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
    combine_conditions_and,
    combine_conditions_or,
    negate_conditions,
)

__all__ = [
    # Types
    "CursorConditionFactory",
    "IntegrityErrorCheck",
    # Integrity
    "parse_integrity_error",
    "match_integrity_error",
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
    "ExistsQuerier",
    # BatchQuerier
    "BatchQuerier",
    "BatchQuerierResult",
    "execute_batch_querier",
    # Creator
    "CreatorSpec",
    "Creator",
    "CreatorResult",
    "execute_creator",
    # DependentCreator
    "DependentCreatorSpec",
    "execute_dependent_creator",
    "execute_bulk_dependent_creator",
    # NextValue
    "NextValuePolicy",
    "execute_next_value_creator",
    # BulkCreator
    "BulkCreator",
    "BulkCreatorError",
    "BulkCreatorResult",
    "BulkCreatorResultWithFailures",
    "execute_bulk_creator",
    "execute_bulk_creator_partial",
    # ConditionalCreator
    "ConditionalCreator",
    "BulkConditionalCreator",
    # Updater
    "UpdaterSpec",
    "Updater",
    "UpdaterResult",
    "execute_updater",
    # ConditionalUpdater
    "ConditionalUpdater",
    "BulkConditionalUpdater",
    # BatchUpdater
    "BatchUpdaterSpec",
    "BatchUpdater",
    "BatchUpdaterResult",
    "execute_batch_updater",
    # BulkUpdater
    "BulkUpdaterError",
    "BulkUpdaterResult",
    "execute_bulk_updater_partial",
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
    # ConditionalPurger
    "ConditionalPurger",
    "BulkConditionalPurger",
    # BulkPurger
    "BulkPurgerError",
    "BulkPurgerResultWithFailures",
    "execute_bulk_purger_partial",
    # BatchPurger
    "BatchPurgerSpec",
    "BatchPurger",
    "BatchPurgerResult",
    "execute_batch_purger",
    # Utils
    "combine_conditions_and",
    "combine_conditions_or",
    "negate_conditions",
]
