import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, Optional, Protocol, TypeVar

import sqlalchemy as sa
from sqlalchemy.sql import Select
from sqlalchemy.sql.elements import BooleanClauseList

from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.exception import InvalidCursorTypeError
from ai.backend.manager.api.gql.base import resolve_global_id
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.base import DEFAULT_PAGE_SIZE, validate_connection_args
from ai.backend.manager.models.gql_relay import ConnectionPaginationOrder
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.types import PaginationOptions


@dataclass
class RepositoryArgs:
    db: ExtendedAsyncSAEngine
    storage_manager: "StorageSessionManager"
    config_provider: "ManagerConfigProvider"
    valkey_stat_client: "ValkeyStatClient"
    valkey_schedule_client: "ValkeyScheduleClient"
    valkey_image_client: "ValkeyImageClient"
    valkey_live_client: "ValkeyLiveClient"


# Generic types for pagination
TModel = TypeVar("TModel")
TData = TypeVar("TData")
TFilters = TypeVar("TFilters")
TOrdering = TypeVar("TOrdering")


@dataclass
class PaginationQueryResult:
    """Result of a pagination query."""

    data_query: Select
    pagination_order: Optional[ConnectionPaginationOrder] = None


class PaginatableModel(Protocol):
    """Protocol for models that can be paginated"""

    id: Any


class FilterApplier(Protocol):
    """Protocol for applying filters to a query"""

    def apply_filters(self, stmt: Select, filters: Any) -> Select:
        """Apply filters to the query statement"""
        ...


class OrderingApplier(Protocol):
    """Protocol for applying ordering to a query"""

    def apply_ordering(
        self, stmt: Select, ordering: Any
    ) -> tuple[Select, list[tuple[sa.Column, bool]]]:
        """Apply ordering to the query statement and return order clauses for cursor pagination"""
        ...


class ModelConverter(Protocol):
    """Protocol for converting model to data objects"""

    def convert_to_data(self, model: Any) -> Any:
        """Convert model instance to data object"""
        ...


class GenericQueryBuilder(Generic[TModel, TData, TFilters, TOrdering]):
    """
    Generic query builder for constructing SQLAlchemy queries with pagination support.
    """

    def __init__(
        self,
        model_class: type[TModel],
        filter_applier: FilterApplier,
        ordering_applier: OrderingApplier,
        model_converter: ModelConverter,
        cursor_type_name: str,
    ):
        self.model_class = model_class
        self.filter_applier = filter_applier
        self.ordering_applier = ordering_applier
        self.model_converter = model_converter
        self.cursor_type_name = cursor_type_name

    def build_lexicographic_cursor_conditions(
        self,
        order_clauses: list[tuple[sa.Column, bool]],
        cursor_uuid: uuid.UUID,
        pagination_order: Optional[ConnectionPaginationOrder],
    ) -> list[BooleanClauseList]:
        """
        Build lexicographic cursor conditions for multiple ordering fields.
        Generic implementation that works with any model.
        """
        if not order_clauses:
            # Handle empty order_clauses case - compare by ID only
            id_column = getattr(self.model_class, "id")
            if pagination_order == ConnectionPaginationOrder.FORWARD:
                return [id_column > cursor_uuid]
            else:
                return [id_column < cursor_uuid]

        conditions = []

        # Cache subqueries to avoid duplication
        subquery_cache = {}

        def get_cursor_value_subquery(column):
            """Get or create cached subquery for cursor value"""
            if column not in subquery_cache:
                id_column = getattr(self.model_class, "id")
                subquery_cache[column] = (
                    sa.select(column).where(id_column == cursor_uuid).scalar_subquery()
                )
            return subquery_cache[column]

        # Build conditions for each level of the lexicographic ordering
        for i in range(len(order_clauses) + 1):  # +1 for the ID field
            condition_parts = []

            # Add equality conditions for all previous fields
            for j in range(i):
                order_column, desc = order_clauses[j]
                cursor_value_subq = get_cursor_value_subquery(order_column)
                condition_parts.append(order_column == cursor_value_subq)

            # Add the inequality condition for the current field
            if i < len(order_clauses):
                # Current field is one of the ordering fields
                order_column, desc = order_clauses[i]
                cursor_value_subq = get_cursor_value_subquery(order_column)

                # Determine the operator based on sort direction and pagination direction
                if pagination_order == ConnectionPaginationOrder.FORWARD:
                    if desc:
                        inequality_cond = order_column < cursor_value_subq
                    else:
                        inequality_cond = order_column > cursor_value_subq
                else:  # BACKWARD
                    if desc:
                        inequality_cond = order_column > cursor_value_subq
                    else:
                        inequality_cond = order_column < cursor_value_subq

                condition_parts.append(inequality_cond)
            else:
                # Final condition: all fields equal, compare by ID
                id_column = getattr(self.model_class, "id")
                if pagination_order == ConnectionPaginationOrder.FORWARD:
                    id_inequality_cond = id_column > cursor_uuid
                else:  # BACKWARD
                    id_inequality_cond = id_column < cursor_uuid

                condition_parts.append(id_inequality_cond)

            # Combine all parts with AND
            if condition_parts:
                if len(condition_parts) == 1:
                    conditions.append(condition_parts[0])
                else:
                    conditions.append(sa.and_(*condition_parts))

        return conditions

    def build_pagination_queries(
        self,
        pagination: PaginationOptions,
        ordering: Optional[TOrdering] = None,
        filters: Optional[TFilters] = None,
        select_options: Optional[list] = None,
    ) -> PaginationQueryResult:
        """
        Returns:
            PaginationQueryResult
        """
        # Build base query
        stmt = sa.select(self.model_class)
        if select_options:
            stmt = stmt.options(*select_options)

        # Apply filters
        if filters is not None:
            stmt = self.filter_applier.apply_filters(stmt, filters)

        offset_based_pagination = pagination.offset
        forward = pagination.forward
        backward = pagination.backward
        pagination_order = None

        # Determine pagination mode
        if offset_based_pagination:
            offset = pagination.offset.offset if pagination.offset is not None else 0
            page_size = (
                offset_based_pagination.limit
                if offset_based_pagination.limit is not None
                else DEFAULT_PAGE_SIZE
            )

            # Apply ordering for offset-based pagination
            if ordering is not None:
                stmt, _ = self.ordering_applier.apply_ordering(stmt, ordering)

            # Default order by id for consistent pagination
            id_column = getattr(self.model_class, "id")
            stmt = stmt.order_by(id_column.asc())

            # Apply pagination
            stmt = stmt.offset(offset).limit(page_size)

        else:
            # Cursor-based pagination
            after = forward.after if forward else None
            first = forward.first if forward else None
            before = backward.before if backward else None
            last = backward.last if backward else None

            connection_args = validate_connection_args(
                after=after,
                first=first,
                before=before,
                last=last,
            )

            cursor_id = connection_args.cursor
            pagination_order = connection_args.pagination_order
            page_size = connection_args.requested_page_size

            # Apply ordering for cursor-based pagination
            order_clauses: list[tuple[sa.Column, bool]] = []
            if ordering is not None:
                stmt, order_clauses = self.ordering_applier.apply_ordering(stmt, ordering)

            # Handle cursor-based pagination
            if cursor_id is not None:
                type_, cursor_id = resolve_global_id(cursor_id)
                if type_ != self.cursor_type_name:
                    raise InvalidCursorTypeError(f"Invalid cursor type: {type_}")

                cursor_uuid = uuid.UUID(cursor_id)

                # Build the lexicographic cursor conditions
                cursor_conditions = self.build_lexicographic_cursor_conditions(
                    order_clauses, cursor_uuid, pagination_order
                )

                # Apply cursor conditions with OR logic
                if cursor_conditions:
                    combined_cursor_condition = sa.or_(*cursor_conditions)
                    stmt = stmt.where(combined_cursor_condition)

            # Apply ordering based on pagination direction
            final_order_clauses = []
            id_column = getattr(self.model_class, "id")

            if pagination_order == ConnectionPaginationOrder.BACKWARD:
                # Reverse ordering for backward pagination
                for order_column, desc in order_clauses:
                    if desc:
                        final_order_clauses.append(order_column.asc())
                    else:
                        final_order_clauses.append(order_column.desc())
                final_order_clauses.append(id_column.desc())
            else:  # FORWARD or None
                for order_column, desc in order_clauses:
                    if desc:
                        final_order_clauses.append(order_column.desc())
                    else:
                        final_order_clauses.append(order_column.asc())
                final_order_clauses.append(id_column.asc())

            stmt = stmt.order_by(*final_order_clauses)

            # Apply limit
            stmt = stmt.limit(page_size)

        return PaginationQueryResult(data_query=stmt, pagination_order=pagination_order)

    def convert_rows_to_data(
        self, rows: list[TModel], pagination_order: Optional[ConnectionPaginationOrder] = None
    ) -> list[TData]:
        """
        Convert model instances to data objects.
        """
        if pagination_order == ConnectionPaginationOrder.BACKWARD:
            rows = list(reversed(rows))

        return [self.model_converter.convert_to_data(row) for row in rows]


T = TypeVar("T", bound="BaseFilterOptions")


class BaseFilterOptions(Protocol):
    """Protocol for filter options that support logical operations"""

    AND: Optional[list[Any]]
    OR: Optional[list[Any]]
    NOT: Optional[list[Any]]


class BaseFilterApplier(ABC, Generic[T]):
    """Base class for applying filters to queries with common logical operations"""

    def apply_filters(self, stmt: Select, filters: T) -> Select:
        """Apply filters to the query statement"""
        condition, stmt = self._build_filter_condition(stmt, filters)
        if condition is not None:
            stmt = stmt.where(condition)
        return stmt

    def _build_filter_condition(self, stmt: Select, filters: T) -> tuple[Optional[Any], Select]:
        """Build a filter condition from FilterOptions, handling logical operations"""
        conditions = []

        # Apply entity-specific filters
        entity_conditions, stmt = self.apply_entity_filters(stmt, filters)
        if entity_conditions:
            conditions.extend(entity_conditions)

        # Combine basic conditions with AND
        base_condition = None
        if conditions:
            base_condition = sa.and_(*conditions)

        # Handle logical operations
        logical_conditions = []

        # Handle AND operation (list-based)
        and_filters = getattr(filters, "AND", None)
        if and_filters is not None:
            and_conditions = []
            for and_filter in and_filters:
                and_condition, stmt = self._build_filter_condition(stmt, and_filter)
                if and_condition is not None:
                    and_conditions.append(and_condition)
            if and_conditions:
                logical_conditions.append(sa.and_(*and_conditions))

        # Handle OR operation (list-based)
        or_filters = getattr(filters, "OR", None)
        if or_filters is not None:
            or_conditions = []
            for or_filter in or_filters:
                or_condition, stmt = self._build_filter_condition(stmt, or_filter)
                if or_condition is not None:
                    or_conditions.append(or_condition)
            if or_conditions:
                combined_or_condition = sa.or_(*or_conditions)
                if base_condition is not None:
                    # Combine base condition OR logical condition
                    base_condition = sa.or_(base_condition, combined_or_condition)
                else:
                    base_condition = combined_or_condition

        # Handle NOT operation (list-based)
        not_filters = getattr(filters, "NOT", None)
        if not_filters is not None:
            not_conditions = []
            for not_filter in not_filters:
                not_condition, stmt = self._build_filter_condition(stmt, not_filter)
                if not_condition is not None:
                    not_conditions.append(not_condition)
            if not_conditions:
                # Apply NOT to the AND combination of all NOT conditions
                logical_conditions.append(~sa.and_(*not_conditions))

        # Combine all conditions
        all_conditions = []
        if base_condition is not None:
            all_conditions.append(base_condition)
        if logical_conditions:
            all_conditions.extend(logical_conditions)

        final_condition = None
        if all_conditions:
            if len(all_conditions) == 1:
                final_condition = all_conditions[0]
            else:
                final_condition = sa.and_(*all_conditions)

        return final_condition, stmt

    @abstractmethod
    def apply_entity_filters(self, stmt: Select, filters: T) -> tuple[list[Any], Select]:
        """Apply entity-specific filters and return list of conditions and updated statement

        Args:
            stmt: The SQL select statement
            filters: The filter options

        Returns:
            Tuple of (list of conditions, updated statement)
        """
        ...


TOrderingOptions = TypeVar("TOrderingOptions", bound="BaseOrderingOptions")


class BaseOrderingOptions(Protocol):
    """Protocol for ordering options"""

    order_by: list[tuple[Any, bool]]


class BaseOrderingApplier(ABC, Generic[TOrderingOptions]):
    """Base class for applying ordering to queries"""

    def apply_ordering(
        self, stmt: Select, ordering: TOrderingOptions
    ) -> tuple[Select, list[tuple[sa.Column, bool]]]:
        """Apply ordering to the query statement and return order clauses for cursor pagination"""
        order_clauses = []
        sql_order_clauses = []

        for field, desc in ordering.order_by:
            order_column = self.get_order_column(field)
            order_clauses.append((order_column, desc))

            if desc:
                sql_order_clauses.append(order_column.desc())
            else:
                sql_order_clauses.append(order_column.asc())

        if sql_order_clauses:
            stmt = stmt.order_by(*sql_order_clauses)

        return stmt, order_clauses

    @abstractmethod
    def get_order_column(self, field: Any) -> sa.Column:
        """Get the SQLAlchemy column for the given field"""
        ...
