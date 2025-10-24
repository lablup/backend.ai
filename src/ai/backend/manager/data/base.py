"""Generic base types and abstract classes for AST converters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Generic, TypeVar

from lark import Tree
from lark.lexer import Token

from ai.backend.manager.models.minilang.queryfilter import _parser as parser

TFilterField = TypeVar("TFilterField", bound=StrEnum)
TFilter = TypeVar("TFilter")


class BaseFilterOperator(StrEnum):
    """Base filter operators supported across domains."""

    EQ = "=="
    NE = "!="
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    CONTAINS = "contains"
    IN = "in"
    ISNOT = "isnot"
    IS = "is"
    LIKE = "like"
    ILIKE = "ilike"


class BaseCombineOperator(StrEnum):
    """Base logical operators for combining filter expressions."""

    AND = "&"
    OR = "|"


@dataclass
class LeafFilterCondition(Generic[TFilterField]):
    """
    Represents a single leaf filter condition.
    """

    field: TFilterField
    operator: BaseFilterOperator
    value: Any


@dataclass
class FilterGroup(Generic[TFilterField]):
    """
    Represents filter conditions with logical operators.
    Can represent both single conditions and combined conditions.
    """

    operator: BaseCombineOperator
    conditions: list[LeafFilterCondition[TFilterField] | FilterGroup[TFilterField]]


class BaseFilterConverter(
    ABC,
    Generic[TFilterField, TFilter],
):
    """
    Abstract base class for converting Lark AST to structured filter objects.

    This class provides the core conversion logic from minilang AST (from QueryFilterParser)
    to domain-specific filter objects that can be used by Service and Repository layers.

    Uses BaseFilterOperator and BaseCombineOperator for all domains to reduce generic complexity.

    Type Parameters:
        TFilterField: Enum type for filter field names (domain-specific)
        TFilter: The final filter type (e.g., AgentFilter)
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
                        BaseFilterConverter._parse_value(child) for child in value_tree.children
                    ]
                case "value":
                    # Nested value wrapper
                    return BaseFilterConverter._parse_value(value_tree.children[0])

        elif isinstance(value_tree, list):
            # Array of values
            return [BaseFilterConverter._parse_value(v) for v in value_tree]

        return value_tree

    @abstractmethod
    def _parse_field(self, field_name: str) -> TFilterField:
        """
        Parse field name string to domain-specific field enum.

        Args:
            field_name: Raw field name from AST

        Returns:
            Domain-specific field enum value

        Raises:
            ValueError: If field name is unknown
        """
        raise NotImplementedError()

    @abstractmethod
    def _convert_filter_group(
        self,
        filter_group: FilterGroup[TFilterField],
    ) -> TFilter:
        """
        Convert generic FilterGroup to domain-specific final filter type.

        This is an internal method that must be implemented by subclasses
        to convert the generic filter structure to their specific filter type.

        Args:
            filter_group: The parsed filter group

        Returns:
            Domain-specific filter object
        """
        raise NotImplementedError()

    def execute(self, expr: str) -> TFilter:
        """
        Convert a Lark AST tree directly to domain-specific filter type.

        This is the main public API for converting AST to filters.
        It internally builds a FilterGroup and then converts it to the final type.

        The AST structure from QueryFilterParser:
        - binary_expr: field operator value (e.g., "id ilike '%test%'")
        - combine_expr: expr operator expr (e.g., "expr1 & expr2")
        - unary_expr: ! expr (e.g., "!status == 'ALIVE'") - NOT SUPPORTED
        - paren_expr: ( expr )

        Args:
            ast: The Lark AST tree from QueryFilterParser._parser.parse()

        Returns:
            Domain-specific filter object

        Raises:
            ValueError: If AST structure is invalid or contains unsupported operators
        """
        ast = parser.parse(expr)
        filter_group = self._ast_to_filter_group(ast)
        return self._convert_filter_group(filter_group)

    def _ast_to_filter_group(
        self,
        ast: Tree,
    ) -> FilterGroup[TFilterField]:
        """
        Convert a Lark AST tree to generic FilterGroup.

        The AST structure from QueryFilterParser:
        - binary_expr: field operator value (e.g., "id ilike '%test%'")
        - combine_expr: expr operator expr (e.g., "expr1 & expr2")
        - unary_expr: ! expr (e.g., "!status == 'ALIVE'") - NOT SUPPORTED
        - paren_expr: ( expr )

        Args:
            ast: The Lark AST tree

        Returns:
            FilterGroup representing the filter (even for single conditions)

        Raises:
            ValueError: If AST structure is invalid or contains unsupported operators
        """
        match ast.data:
            case "binary_expr":
                # Single filter expression: field operator value
                # Convert to a Group with one condition
                field_token = ast.children[0]
                operator_token = ast.children[1]
                if not isinstance(field_token, Token) or not isinstance(operator_token, Token):
                    raise ValueError("Invalid AST structure for binary expression")

                field_name = str(field_token.value)
                operator = str(operator_token.value)
                value = self._parse_value(ast.children[2])

                # Parse to domain-specific field enum and base operator enum
                field = self._parse_field(field_name)
                operator_enum = BaseFilterOperator(operator)

                # Default combine operator (AND for single conditions)
                default_combine_op = BaseCombineOperator.AND

                # Return as a Group with single condition
                return FilterGroup(
                    operator=default_combine_op,
                    conditions=[
                        LeafFilterCondition(
                            field=field,
                            operator=operator_enum,
                            value=value,
                        )
                    ],
                )

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
                    raise ValueError("Invalid AST structure for combine expression")

                # Recursively process left and right
                left_group = self._ast_to_filter_group(left_tree)
                right_group = self._ast_to_filter_group(right_tree)
                combine_op = str(combine_op_token.value)

                # Map combine operator to base enum
                combine_op_enum = BaseCombineOperator(combine_op)

                # Flatten if left side has the same operator
                conditions: list[LeafFilterCondition[TFilterField] | FilterGroup[TFilterField]]
                if left_group.operator == combine_op_enum:
                    # Flatten: merge left's conditions
                    conditions = left_group.conditions + [right_group]
                else:
                    conditions = [left_group, right_group]

                return FilterGroup(
                    operator=combine_op_enum,
                    conditions=conditions,
                )

            case "unary_expr":
                # NOT operator is not supported
                raise ValueError("NOT operator (!) is not supported in this implementation")

            case "paren_expr":
                # Parenthesized expression: ( expr )
                return self._ast_to_filter_group(ast.children[0])

            case _:
                raise ValueError(f"Unknown AST node type: {ast.data}")


TOrderBy = TypeVar("TOrderBy")
TOrderField = TypeVar("TOrderField", bound=StrEnum)


class BaseOrderConverter(ABC, Generic[TOrderField, TOrderBy]):
    """
    Abstract base class for parsing order expressions.

    Parses order strings like "+id,-status" into domain-specific OrderBy objects.

    Type Parameters:
        TOrderField: Enum type for order field names (domain-specific)
        TOrderBy: Domain-specific OrderBy type (e.g., AgentOrderBy)

    Usage:
        class MyOrderParser(BaseOrderParser[MyOrderField, MyOrderBy]):

            def _create_order_by(self, field: MyOrderField, ascending: bool) -> MyOrderBy:
                return MyOrderBy(field=field, ascending=ascending)
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
            raise ValueError("Order expression cannot be empty")
        result = {}
        for expr in expr_list:
            # Check for prefix
            if expr[0] in ("+", "-"):
                ascending = expr[0] == "+"
                field_name = expr[1:].strip()
            else:
                # Default to ascending if no prefix
                ascending = True
                field_name = expr
            if field_name == "":
                raise ValueError("Field name in order expression cannot be empty")
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
    def _create_order_by(self, order_by: dict[TOrderField, bool]) -> list[TOrderBy]:
        """
        Create domain-specific OrderBy object.
        Args:
            order_by: Dict mapping domain-specific field enums to ascending bool
        Returns:
            List of domain-specific OrderBy objects
        """
        raise NotImplementedError()

    def execute(self, order_expr: str) -> list[TOrderBy]:
        """
        Parse order expression string to list of domain-specific OrderBy objects.

        Format: "+field" or "-field"
        - '+' or no prefix means ascending
        - '-' means descending

        Args:
            order_expr: Order expression string (e.g., "+id", "-status")

        Returns:
            List containing single OrderBy object

        Raises:
            ValueError: If expression is invalid or empty
        """
        raw_orders = self._parse_raw_expr(order_expr)
        converted_orders = self._convert_field(raw_orders)

        return self._create_order_by(order_by=converted_orders)
