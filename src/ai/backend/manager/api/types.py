from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncContextManager,
    Awaitable,
    Callable,
    Generic,
    Iterable,
    Mapping,
    Self,
    Tuple,
    TypeVar,
)

import aiohttp_cors
from aiohttp import web
from aiohttp.typedefs import Middleware
from lark import Tree
from lark.lexer import Token
from typing_extensions import TypeAlias

from ai.backend.common.exception import ASTParsingFailed, InvalidParameter, UnsupportedOperation
from ai.backend.manager.api.gql.base import StringFilter

if TYPE_CHECKING:
    from .context import RootContext


WebRequestHandler: TypeAlias = Callable[
    [web.Request],
    Awaitable[web.StreamResponse],
]
WebMiddleware: TypeAlias = Middleware

CORSOptions: TypeAlias = Mapping[str, aiohttp_cors.ResourceOptions]
AppCreator: TypeAlias = Callable[
    [CORSOptions],
    Tuple[web.Application, Iterable[WebMiddleware]],
]

CleanupContext: TypeAlias = Callable[["RootContext"], AsyncContextManager[None]]


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
                        case _:
                            return value_tree.value
                case _:
                    raise ASTParsingFailed(f"Unknown token type in value: {value_tree.type}")

        if isinstance(value_tree, Tree):
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
                case _:
                    raise ASTParsingFailed(f"Unknown tree type in value: {value_tree.data}")

        if isinstance(value_tree, list):
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
                if str_value.endswith("%"):
                    return StringFilter(starts_with=str_value[:-1])
                if str_value.startswith("%"):
                    return StringFilter(ends_with=str_value[1:])
                return StringFilter(equals=str_value)
            case "ilike":
                # Parse ILIKE pattern (case-insensitive)
                if str_value.startswith("%") and str_value.endswith("%"):
                    return StringFilter(i_contains=str_value[1:-1])
                if str_value.endswith("%"):
                    return StringFilter(i_starts_with=str_value[:-1])
                if str_value.startswith("%"):
                    return StringFilter(i_ends_with=str_value[1:])
                return StringFilter(i_equals=str_value)
            case _:
                raise UnsupportedOperation(f"Unsupported string operator: {operator}")

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
TOrderingOptions = TypeVar("TOrderingOptions")


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
