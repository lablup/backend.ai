"""Streaming export types and utilities for server-side CSV export.

This module provides the core types and functions for streaming export functionality.
Based on BEP-1025: Server-Side CSV Export API.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Any

import sqlalchemy as sa

from .types import QueryCondition, QueryOrder

if TYPE_CHECKING:
    from sqlalchemy.orm.attributes import InstrumentedAttribute

    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class ExportLimitExceeded(Exception):
    """Raised when export row limit is exceeded."""

    pass


class ExportFieldType(StrEnum):
    """Export field type for client display and validation."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    UUID = "uuid"
    JSON = "json"
    ENUM = "enum"


# Formatter type definition - converts any value to string for CSV
type ExportFormatter = Callable[[Any], str]


@dataclass(frozen=True)
class JoinDef:
    """JOIN definition for export queries.

    Defines a table and condition for LEFT JOIN operations.
    Used by ExportFieldDef to declare required joins for a field.

    Attributes:
        table: Table to join (e.g., ProjectResourcePolicyRow.__table__)
        condition: JOIN condition as SQLAlchemy expression
    """

    table: sa.FromClause
    condition: sa.ColumnElement[bool]


@dataclass(frozen=True)
class ExportFieldDef:
    """Export field definition.

    Informs clients which fields can be selected,
    and used for actual data transformation.

    Attributes:
        key: Field identifier (used in API requests)
        name: Name displayed in CSV header
        description: Field description (displayed in client UI)
        field_type: Field type for client display
        column: ORM column reference for SELECT query building
        formatter: Custom formatter (None uses default conversion)
        joins: Set of JoinDef required to access this field (None = no joins needed)
    """

    key: str
    name: str
    description: str
    field_type: ExportFieldType
    column: InstrumentedAttribute[Any]
    formatter: ExportFormatter | None = None
    joins: tuple[JoinDef, ...] | frozenset[JoinDef] | None = None


@dataclass(frozen=True)
class ExportQueryParams:
    """Input parameters for export query (without fields).

    Used by API layer to pass query parameters to the service.
    Service constructs the full StreamingExportQuery by adding fields.

    Attributes:
        conditions: WHERE clause conditions
        orders: ORDER BY clause sort conditions
        max_rows: Maximum export row count (passed from config.export.max_rows)
        statement_timeout_sec: DB statement timeout (passed from config.export.statement_timeout_sec)
    """

    conditions: list[QueryCondition]
    orders: list[QueryOrder]
    max_rows: int
    statement_timeout_sec: int


@dataclass(frozen=True)
class StreamingExportQuery:
    """Query definition for streaming export.

    Similar to BatchQuerier but streams all data without pagination.
    Limits export size with max_rows.

    Attributes:
        select_from: FROM clause (single table or joined tables)
        fields: Selected field definitions for SELECT query building
        conditions: WHERE clause conditions
        orders: ORDER BY clause sort conditions
        max_rows: Maximum export row count (passed from config.export.max_rows)
        statement_timeout_sec: DB statement timeout (passed from config.export.statement_timeout_sec)
    """

    select_from: sa.FromClause
    fields: list[ExportFieldDef]
    conditions: list[QueryCondition]
    orders: list[QueryOrder]
    max_rows: int
    statement_timeout_sec: int

    @classmethod
    def from_params(
        cls,
        params: ExportQueryParams,
        select_from: sa.FromClause,
        fields: list[ExportFieldDef],
    ) -> StreamingExportQuery:
        """Create StreamingExportQuery from params, select_from, and fields."""
        return cls(
            select_from=select_from,
            fields=fields,
            conditions=params.conditions,
            orders=params.orders,
            max_rows=params.max_rows,
            statement_timeout_sec=params.statement_timeout_sec,
        )


@dataclass
class ReportDef:
    """Export report definition.

    Defines available fields for export.

    Attributes:
        report_key: Report identifier (e.g., "audit-logs")
        name: Report name for display
        description: Report description
        select_from: FROM clause (single table or joined tables)
        fields: Available field list
    """

    report_key: str
    name: str
    description: str
    select_from: sa.FromClause
    fields: list[ExportFieldDef]

    def get_field(self, key: str) -> ExportFieldDef | None:
        """Find field definition by key."""
        for f in self.fields:
            if f.key == key:
                return f
        return None

    def get_field_keys(self) -> set[str]:
        """Return all field keys."""
        return {f.key for f in self.fields}

    def validate_field_keys(self, requested_keys: list[str]) -> list[str]:
        """Return invalid field keys."""
        valid_keys = self.get_field_keys()
        return [k for k in requested_keys if k not in valid_keys]

    def get_fields_by_keys(self, keys: list[str]) -> list[ExportFieldDef]:
        """Return field definitions for the given keys, preserving order."""
        key_to_field = {f.key: f for f in self.fields}
        return [key_to_field[k] for k in keys if k in key_to_field]


DEFAULT_PARTITION_SIZE = 1000


async def execute_streaming_export(
    db: ExtendedAsyncSAEngine,
    query: StreamingExportQuery,
    partition_size: int = DEFAULT_PARTITION_SIZE,
) -> AsyncIterator[Sequence[Sequence[Any]]]:
    """Execute streaming export based on query definition.

    Uses db_sess.stream() for server-side cursor data streaming.
    Builds SELECT query from field column references in query.fields.
    Yields rows in partitions for better performance.

    Args:
        db: Database engine
        query: Export query containing fields, conditions, orders, max_rows, statement_timeout_sec
        partition_size: Number of rows per partition (default: 1000)

    Yields:
        Partitions of row values (each row in query.fields order)
    """
    # Build SELECT from field columns with explicit FROM clause
    columns = [f.column for f in query.fields]
    base_query = sa.select(*columns).select_from(query.select_from)

    # Apply conditions
    for condition in query.conditions:
        base_query = base_query.where(condition())

    # Apply ordering
    for order in query.orders:
        base_query = base_query.order_by(order)

    # Apply max_rows LIMIT
    base_query = base_query.limit(query.max_rows)

    async with db.begin_readonly_session_read_committed() as db_sess:
        # Set statement timeout
        await db_sess.execute(sa.text(f"SET statement_timeout = '{query.statement_timeout_sec}s'"))

        # Server-side cursor streaming with partitions
        result = await db_sess.stream(base_query)

        async for partition in result.partitions(partition_size):
            yield [_transform_row(row, query.fields) for row in partition]


def _transform_row(
    row: sa.Row[Any],
    fields: list[ExportFieldDef],
) -> list[Any]:
    """Transform row to list of values in field order."""
    result: list[Any] = []
    for i, field_def in enumerate(fields):
        value = row[i]
        # Apply custom formatter if present
        if field_def.formatter is not None:
            value = field_def.formatter(value)
        result.append(value)
    return result


@dataclass(frozen=True)
class ExportDataStream:
    """Export data stream with field information.

    Bundles field names and data iterator for streaming export.
    Yields partitions of row values for efficient async processing.
    """

    field_names: list[str]
    reader: AsyncIterator[Sequence[Sequence[Any]]]  # partitions of row values
