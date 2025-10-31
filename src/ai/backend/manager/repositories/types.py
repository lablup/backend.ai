import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Generic, Optional, Protocol, Self, TypeVar

import sqlalchemy as sa
from lark import Tree
from lark.lexer import Token
from sqlalchemy.sql import Select
from sqlalchemy.sql.elements import BooleanClauseList

from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.exception import ASTParsingFailed, InvalidCursorTypeError, InvalidParameter
from ai.backend.manager.api.gql.base import StringFilter, resolve_global_id
from ai.backend.manager.clients.valkey_client.valkey_image.client import ValkeyImageClient
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


class BaseMinilangFilterConverter(ABC):
    """
    Abstract base class for converting minilang filter expressions to domain Filter objects.

    This class converts string-based filter expressions (minilang) into structured Filter
    objects by parsing the AST and mapping fields to domain-specific filter types.

    Domain-specific Filter classes MUST inherit from this and implement
    the _create_from_condition() method.

    Conversion flow:
        1. Parse minilang string expression → AST (Lark Tree)
        2. Convert AST → Filter object structure with field mappings
        3. Support logical operations (AND, OR) for complex filters

    Example:
        @dataclass
        class AgentFilter(BaseMinilangFilterConverter):
            id: Optional[StringFilter] = None
            status: Optional[AgentStatusFilter] = None

            AND: Optional[list[Self]] = None
            OR: Optional[list[Self]] = None
            NOT: Optional[list[Self]] = None

            @classmethod
            def from_minilang(cls, expr: str) -> AgentFilter:
                '''Convert minilang expression like "id ilike '%abc%' & status == 'ALIVE'" to AgentFilter'''
                from ai.backend.manager.models.minilang.queryfilter import _parser as parser
                ast = parser.parse(expr)
                return cls._from_ast(ast)

            @classmethod
            def _create_from_condition(cls, field: str, operator: str, value: Any) -> Self:
                match field.lower():
                    case "id":
                        return cls(id=cls._create_string_filter(operator, value))
                    case _:
                        raise ValueError(f"Unsupported filter field: {field}")
    """

    @staticmethod
    def _parse_value(value_tree: Tree | Token | list | Any) -> Any:
        """
        Extract the actual value from the AST value node.

        Args:
            value_tree: AST node representing a value (string, number, atom, array)

        Returns:
            Parsed Python value (str, int, float, bool, None, or list)
        """
        if isinstance(value_tree, Token):
            # Direct token (e.g., string, number)
            token_value: str = str(value_tree.value)
            match value_tree.type:
                case "ESCAPED_STRING":
                    # Remove quotes and unescape
                    return token_value[1:-1].replace('\\"', '"')
                case "SIGNED_NUMBER":
                    # Parse number
                    if "." in token_value:
                        return float(token_value)
                    return int(token_value)
                case "ATOM":
                    # Atom values like null, true, false
                    match token_value:
                        case "null":
                            return None
                        case "true":
                            return True
                        case "false":
                            return False
            return value_tree.value

        elif isinstance(value_tree, Tree):
            match value_tree.data:
                case "string":
                    # String value
                    token = value_tree.children[0]
                    if isinstance(token, Token):
                        token_value = str(token.value)
                        return token_value[1:-1].replace('\\"', '"')
                case "number":
                    # Number value
                    token = value_tree.children[0]
                    if isinstance(token, Token):
                        token_value = str(token.value)
                        if "." in token_value:
                            return float(token_value)
                        return int(token_value)
                case "atom":
                    # Atomic value
                    token = value_tree.children[0]
                    if isinstance(token, Token):
                        token_value = str(token.value)
                        match token_value:
                            case "null":
                                return None
                            case "true":
                                return True
                            case "false":
                                return False
                case "array":
                    # Array value
                    return [
                        BaseMinilangFilterConverter._parse_value(child)
                        for child in value_tree.children
                    ]
                case "value":
                    # Nested value wrapper
                    return BaseMinilangFilterConverter._parse_value(value_tree.children[0])

        elif isinstance(value_tree, list):
            # Array of values
            return [BaseMinilangFilterConverter._parse_value(v) for v in value_tree]

        return value_tree

    @staticmethod
    def _create_string_filter(operator: str, value: Any) -> StringFilter:
        """
        Create StringFilter from operator and value.

        Args:
            operator: Operator string (e.g., "==", "!=", "like", "ilike", "contains")
            value: String value to filter

        Returns:
            StringFilter with appropriate filter type
        """
        str_value = str(value)

        match operator:
            case "==":
                return StringFilter(equals=str_value)
            case "!=":
                return StringFilter(not_equals=str_value)
            case "contains":
                return StringFilter(contains=str_value)
            case "like":
                # Parse LIKE pattern: %value% -> contains, value% -> starts_with, %value -> ends_with
                if str_value.startswith("%") and str_value.endswith("%"):
                    return StringFilter(contains=str_value[1:-1])
                elif str_value.endswith("%"):
                    return StringFilter(starts_with=str_value[:-1])
                elif str_value.startswith("%"):
                    return StringFilter(ends_with=str_value[1:])
                else:
                    return StringFilter(equals=str_value)
            case "ilike":
                # Parse ILIKE pattern (case-insensitive)
                if str_value.startswith("%") and str_value.endswith("%"):
                    return StringFilter(i_contains=str_value[1:-1])
                elif str_value.endswith("%"):
                    return StringFilter(i_starts_with=str_value[:-1])
                elif str_value.startswith("%"):
                    return StringFilter(i_ends_with=str_value[1:])
                else:
                    return StringFilter(i_equals=str_value)
            case _:
                # Default to equals for unknown operators
                return StringFilter(equals=str_value)

    @classmethod
    @abstractmethod
    def _create_from_condition(cls, field: str, operator: str, value: Any) -> Self:
        """
        Create Filter instance with single condition from field, operator, and value.

        Args:
            field: Field name (e.g., "id", "status", "region")
            operator: Operator string (e.g., "==", "!=", "ilike")
            value: Filter value

        Returns:
            Filter instance of the calling class type

        Raises:
            ValueError: If field name is not supported

        Note:
            Subclasses MUST implement this method to map field names
            to their specific filter structure.
        """
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def from_minilang(cls, expr: str) -> Self:
        """
        Convert minilang expression string to Filter object.

        Args:
            expr: Minilang filter expression string

        Returns:
            Filter object of the calling class type
        """
        raise NotImplementedError()

    @classmethod
    def _from_ast(cls, ast: Tree) -> Self:
        """
        Convert Lark AST to Filter object recursively.

        This is a common implementation that all domain filters can use.
        Subclasses must implement _create_from_condition(field, operator, value)
        and have AND/OR/NOT fields for logical operations.

        Args:
            ast: Parsed AST tree from minilang parser

        Returns:
            Filter object of the calling class type

        Note:
            The calling class must have:
            - _create_from_condition(field: str, operator: str, value: Any) classmethod (abstract)
            - AND: Optional[list[Self]] field
            - OR: Optional[list[Self]] field
            - NOT: Optional[list[Self]] field (optional)
        """
        match ast.data:
            case "binary_expr":
                # Single filter expression: field operator value
                field_token = ast.children[0]
                operator_token = ast.children[1]
                if not isinstance(field_token, Token) or not isinstance(operator_token, Token):
                    raise ASTParsingFailed("Invalid AST structure for binary expression")

                field_name = str(field_token.value)
                operator = str(operator_token.value)
                value = cls._parse_value(ast.children[2])

                # Call domain-specific field mapping
                return cls._create_from_condition(field_name, operator, value)

            case "combine_expr":
                # Combined expression: expr & expr or expr | expr
                left_tree = ast.children[0]
                combine_op_token = ast.children[1]
                right_tree = ast.children[2]

                if (
                    not isinstance(left_tree, Tree)
                    or not isinstance(combine_op_token, Token)
                    or not isinstance(right_tree, Tree)
                ):
                    raise ASTParsingFailed("Invalid AST structure for combine expression")

                left_filter = cls._from_ast(left_tree)
                right_filter = cls._from_ast(right_tree)
                combine_op = str(combine_op_token.value)

                match combine_op:
                    case "&":
                        return cls(AND=[left_filter, right_filter])  # type: ignore[call-arg]
                    case "|":
                        return cls(OR=[left_filter, right_filter])  # type: ignore[call-arg]
                    case _:
                        raise ASTParsingFailed(f"Unknown combine operator: {combine_op}")

            case "unary_expr":
                raise ASTParsingFailed("NOT operator (!) is not supported in this implementation")

            case "paren_expr":
                # Parenthesized expression: ( expr )
                return cls._from_ast(ast.children[0])

            case _:
                raise ASTParsingFailed(f"Unknown AST node type: {ast.data}")


TOrderField = TypeVar("TOrderField", bound=StrEnum)


class BaseMinilangOrderParser(ABC, Generic[TOrderField, TOrderingOptions]):
    """
    Abstract base class for parsing order expressions into OrderingOption objects.

    This class converts string-based order expressions (e.g., "+id,-status") into
    OrderingOption objects by parsing the field names, directions, and mapping
    to domain-specific field enums.

    Conversion flow:
        1. Parse order string expression → dict of field names to ascending bool
        2. Convert field names → domain-specific field enums (e.g., AgentOrderField)
        3. Create OrderingOption with list of (field, desc) tuples

    Type Parameters:
        TOrderField: Enum type for order field names (domain-specific)
        TOrderingOptions: Domain-specific OrderingOption type (e.g., AgentOrderingOptions)

    Example:
        class AgentOrderParser(BaseOrderParser[AgentOrderField, AgentOrderingOptions]):

            def _convert_field(self, parsed_expr: dict[str, bool]) -> dict[AgentOrderField, bool]:
                return {AgentOrderField(name): asc for name, asc in parsed_expr.items()}

            def _create_ordering_option(self, order_by: dict[AgentOrderField, bool]) -> AgentOrderingOptions:
                # Convert to list of (field, desc) tuples where desc = not ascending
                order_list = [(field, not asc) for field, asc in order_by.items()]
                return AgentOrderingOptions(order_by=order_list)
    """

    def _parse_raw_expr(self, order_expr: str) -> dict[str, bool]:
        """
        Parse raw order expression string to dict of field name to ascending bool.
        Args:
            order_expr: Order expression string (e.g., "+id,-status")
        Returns:
            Dict mapping raw field names to ascending bool (True=asc, False=desc)
        """

        expr_list = [expr.strip() for expr in order_expr.split(",") if expr.strip()]
        if not expr_list:
            raise InvalidParameter("Order expression cannot be empty")
        result = {}
        for expr in expr_list:
            # Check for prefix
            if expr and expr[0] in ("+", "-"):
                ascending = expr[0] == "+"
                field_name = expr[1:].strip()
            else:
                # Default to ascending if no prefix
                ascending = True
                field_name = expr
            if field_name == "":
                raise InvalidParameter("Field name in order expression cannot be empty")
            result[field_name] = ascending
        return result

    @abstractmethod
    def _convert_field(self, parsed_expr: dict[str, bool]) -> dict[TOrderField, bool]:
        """
        Convert raw field names to domain-specific field enums.

        Args:
            parsed_expr: Dict mapping raw field names to ascending bool

        Returns:
            Dict mapping domain-specific field enums to ascending bool
        """
        raise NotImplementedError()

    @abstractmethod
    def _create_ordering_option(self, order_by: dict[TOrderField, bool]) -> TOrderingOptions:
        """
        Create domain-specific OrderingOption object.
        Args:
            order_by: Dict mapping domain-specific field enums to ascending bool
        Returns:
            OrderingOption object with list of (field, desc) tuples
        """
        raise NotImplementedError()

    def from_minilang(self, order_expr: str) -> TOrderingOptions:
        """
        Parse order expression string from minilang to OrderingOption object.

        Format: "+field" or "-field"
        - '+' or no prefix means ascending
        - '-' means descending

        Args:
            order_expr: Order expression string (e.g., "+id", "-status")

        Returns:
            OrderingOption object

        Raises:
            ValueError: If expression is invalid or empty
        """
        raw_orders = self._parse_raw_expr(order_expr)
        converted_orders = self._convert_field(raw_orders)

        return self._create_ordering_option(order_by=converted_orders)
