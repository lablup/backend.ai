"""Read-side types and utilities for the repository layer.

Re-exports all public APIs for backward compatibility.
"""

from ai.backend.manager.models.specs.lookup import DataLookup
from ai.backend.manager.models.specs.pagination import (
    CursorBackwardPagination,
    CursorForwardPagination,
    NoPagination,
    OffsetPagination,
    PageInfoResult,
    QueryPagination,
)
from ai.backend.manager.models.specs.querier import DataQuerier
from ai.backend.manager.models.specs.searcher import (
    Searcher,
    SearcherResult,
)
from ai.backend.manager.models.specs.types import (
    IntegrityErrorCheck,
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
from .querier import (
    BatchQuerier,
    BatchQuerierResult,
    BatchQueryOptions,
    Querier,
    QuerierResult,
    execute_batch_querier,
    execute_querier,
)
from .types import (
    CursorConditionFactory,
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
    "DataLookup",
    "DataQuerier",
    "Querier",
    "QuerierResult",
    "execute_querier",
    # BatchQuerier
    "BatchQuerier",
    "BatchQuerierResult",
    "BatchQueryOptions",
    "execute_batch_querier",
    # Searcher
    "Searcher",
    "SearcherResult",
]
