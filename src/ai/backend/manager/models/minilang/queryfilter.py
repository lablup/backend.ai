from typing import Any, Mapping, Optional, Type, TypeAlias, Union

import sqlalchemy as sa
from lark import Lark, LarkError, Transformer, Tree
from lark.lexer import Token

from . import (
    ArrayFieldItem,
    EnumFieldItem,
    FieldSpecItem,
    JSONFieldItem,
    ORMFieldItem,
    get_col_from_table,
)

__all__ = (
    "FieldSpecType",
    "FilterableSQLQuery",
    "QueryFilterParser",
)

_grammar = r"""
    ?start: expr
    value: string
           | number
           | array
           | ATOM -> atom
    ATOM       : "null" | "true" | "false"
    COMBINE_OP : "&" | "|"
    UNARY_OP   : "!"
    BINARY_OP  : "==" | "!="
               | ">" | ">="
               | "<" | "<="
               | "contains" | "in"
               | "isnot" | "is"
               | "like" | "ilike"
    expr: UNARY_OP expr         -> unary_expr
        | CNAME BINARY_OP value -> binary_expr
        | expr COMBINE_OP expr  -> combine_expr
        | "(" expr ")"          -> paren_expr
    array  : "[" [value ("," value)*] "]"
    string : ESCAPED_STRING
    number : SIGNED_NUMBER
    %import common.CNAME
    %import common.ESCAPED_STRING
    %import common.SIGNED_NUMBER
    %import common.WS
    %ignore WS
"""
_parser = Lark(
    _grammar,
    parser="lalr",
    maybe_placeholders=False,
)

FilterableSQLQuery = Union[sa.sql.Select, sa.sql.Update, sa.sql.Delete]
FieldSpecType: TypeAlias = Mapping[str, FieldSpecItem] | None
WhereClauseType: TypeAlias = (
    sa.sql.expression.BinaryExpression | sa.sql.expression.BooleanClauseList
)


class QueryFilterTransformer(Transformer):
    def __init__(
        self,
        sa_table: sa.Table,
        fieldspec: Optional[FieldSpecType] = None,
        exclude_fields: Optional[set[str]] = None,
    ) -> None:
        super().__init__()
        self._sa_table = sa_table
        self._fieldspec = fieldspec
        self._exclude_fields = exclude_fields or set()

    def string(self, token: list[Token]) -> str:
        s = token[0]
        # SQL-side escaping is handled by SQLAlchemy
        return s[1:-1].replace('\\"', '"')

    def number(self, token: list[Token]) -> int | float:
        n = token[0]
        if "." in n:
            return float(n)
        return int(n)

    array = list

    def atom(self, token: list[Token]) -> Type[sa.sql.elements.SingletonConstant]:
        a = token[0]
        if a.value == "null":
            return sa.null()
        elif a.value == "true":
            return sa.true()
        elif a.value == "false":
            return sa.false()
        raise ValueError("Unknown/unsupported atomic token", a.value)

    def _transform_val_leaf(self, col_name: str, op: str, value: Any) -> Any:
        if self._fieldspec:
            try:
                func = self._fieldspec[col_name][1]
            except KeyError:
                raise ValueError("Unknown/unsupported field name", col_name)
            return func(value) if func is not None else value
        else:
            return value

    def _transform_val(self, col_name: str, op: str, value: Any) -> Any:
        if isinstance(value, Tree):
            val = self._transform_val(col_name, op, value.children[0])
        elif isinstance(value, list):
            val = [self._transform_val(col_name, op, v) for v in value]
        else:
            val = self._transform_val_leaf(col_name, op, value)
        return val

    def binary_expr(self, *args) -> sa.sql.elements.BinaryExpression | None:
        children: list[Token] = args[0]
        col_name = children[0].value
        op = children[1].value

        # If this field is excluded, return None as a sentinel value
        # The combine_expr will handle None appropriately for AND/OR operations
        if col_name in self._exclude_fields:
            return None

        val = self._transform_val(col_name, op, children[2])

        def build_expr(op: str, col, val):
            match op:
                case "==":
                    expr = col == val
                case "!=":
                    expr = col != val
                case ">":
                    expr = col > val
                case ">=":
                    expr = col >= val
                case "<":
                    expr = col < val
                case "<=":
                    expr = col <= val
                case "contains":
                    expr = col.contains(val)
                case "in":
                    expr = col.in_(val)
                case "isnot":
                    expr = col.isnot(val)
                case "is":
                    expr = col.is_(val)
                case "like":
                    expr = col.like(val)
                case "ilike":
                    expr = col.ilike(val)
                case _:
                    expr = args
            return expr

        try:
            if self._fieldspec is not None:
                match self._fieldspec[children[0].value][0]:
                    case ArrayFieldItem(col_name):
                        # For array columns, let's apply the expression on every item,
                        # and select the row if anyone makes the result true.
                        col = get_col_from_table(self._sa_table, col_name)
                        unnested_col = sa.func.unnest(col).alias("item")
                        subq = (
                            sa.select([sa.column("item")])
                            .select_from(unnested_col)
                            .where(build_expr(op, sa.column("item"), val))
                        )
                        expr = sa.exists(subq)
                    case JSONFieldItem(col_name, obj_key):
                        # For json columns, we additionally indicate the object key
                        # to retrieve the value used in the expression.
                        col = get_col_from_table(self._sa_table, col_name).op("->>")(obj_key)
                        expr = build_expr(op, col, val)
                    case EnumFieldItem(col_name, enum_cls):
                        col = get_col_from_table(self._sa_table, col_name)
                        # allow both key and value of enum to be specified on variable `val`
                        # fetch original enum pointer from given `val`
                        try:
                            enum_val = enum_cls(val)
                        except ValueError:
                            try:
                                enum_val = enum_cls[val]
                            except KeyError:
                                raise ValueError(f"Invalid enum value: {val}")
                        expr = build_expr(op, col, enum_val)
                    case ORMFieldItem(column):
                        expr = build_expr(op, column, val)
                    case str(col_name):
                        col = get_col_from_table(self._sa_table, col_name)
                        expr = build_expr(op, col, val)
            else:
                col = get_col_from_table(self._sa_table, col_name)
                expr = build_expr(op, col, val)
        except KeyError:
            raise ValueError("Unknown/unsupported field name", col_name)
        return expr

    def unary_expr(self, *args):
        children = args[0]
        op = children[0].value
        expr = children[1]
        if op in ("not", "!"):
            return sa.not_(expr)
        return args

    def combine_expr(self, *args):
        children = args[0]
        op = children[1].value
        expr1 = children[0]
        expr2 = children[2]

        # Handle None operands (excluded fields) to preserve logical identity
        if op == "&":
            # For AND: if one side is None, return the other (None & x = x)
            if expr1 is None and expr2 is None:
                return sa.true()  # Both excluded -> neutral for AND
            if expr1 is None:
                return expr2
            if expr2 is None:
                return expr1
            return sa.and_(expr1, expr2)
        elif op == "|":
            # For OR: if one side is None, return the other (None | x = x)
            if expr1 is None and expr2 is None:
                return sa.false()  # Both excluded -> neutral for OR
            if expr1 is None:
                return expr2
            if expr2 is None:
                return expr1
            return sa.or_(expr1, expr2)
        return args

    def paren_expr(self, *args):
        children = args[0]
        return children[0]


class QueryFilterParser:
    def __init__(self, fieldspec: Optional[FieldSpecType] = None) -> None:
        self._fieldspec = fieldspec
        self._parser = _parser

    def has_field(self, filter_expr: str, field_name: str) -> bool:
        """
        Check if a filter expression contains a specific field name by parsing the AST.

        This method avoids false positives from naive substring matching (e.g.,
        "project_name" appearing in string literals like "my_project_name_tag").

        Uses iterative traversal instead of recursion to avoid RecursionError
        with deeply nested filter expressions.

        Args:
            filter_expr: Filter expression string to parse
            field_name: Field name to search for

        Returns:
            True if the field is actually referenced in the filter expression
        """
        try:
            ast = self._parser.parse(filter_expr)

            # Use iterative BFS/DFS traversal to avoid recursion depth issues
            stack: list[Tree | Token] = [ast]
            while stack:
                node = stack.pop()
                if isinstance(node, Token):
                    # Check if this is a field name token (CNAME)
                    if node.type == "CNAME" and node.value == field_name:
                        return True
                elif isinstance(node, Tree):
                    # Add all children to the stack for processing
                    stack.extend(node.children)
            return False
        except LarkError:
            # If parsing fails, return False to avoid unnecessary operations
            return False

    def parse_filter(
        self,
        table,
        filter_expr: str,
        *,
        exclude_fields: Optional[set[str]] = None,
    ) -> WhereClauseType:
        """
        Parse filter expression and build WHERE clause.

        Args:
            table: SQLAlchemy table to parse against
            filter_expr: Filter expression string
            exclude_fields: Optional set of field names to exclude from parsing.
                          Fields in this set will be ignored during parsing.

        Returns:
            WHERE clause for SQLAlchemy query
        """
        try:
            ast = self._parser.parse(filter_expr)
            # Pass exclude_fields to transformer so it can skip generating SQL for them
            # but keep them in fieldspec for validation
            where_clause = QueryFilterTransformer(table, self._fieldspec, exclude_fields).transform(
                ast
            )
        except LarkError as e:
            raise ValueError(f"Query filter parsing error: {e}")
        return where_clause

    def append_filter(
        self,
        sa_query: FilterableSQLQuery,
        filter_expr: str,
        *,
        exclude_fields: Optional[set[str]] = None,
    ) -> FilterableSQLQuery:
        """
        Parse the given filter expression and build the where clause based on the first target table from
        the given SQLAlchemy query object.

        Args:
            sa_query: SQLAlchemy query object
            filter_expr: Filter expression string
            exclude_fields: Optional set of field names to exclude from parsing

        Returns:
            Updated SQLAlchemy query with WHERE clause
        """
        if isinstance(sa_query, sa.sql.Select):
            table = sa_query.froms[0]
        elif isinstance(sa_query, sa.sql.Delete):
            table = sa_query.table
        elif isinstance(sa_query, sa.sql.Update):
            table = sa_query.table
        else:
            raise ValueError("Unsupported SQLAlchemy query object type")
        where_clause = self.parse_filter(table, filter_expr, exclude_fields=exclude_fields)
        final_query = sa_query.where(where_clause)
        assert final_query is not None
        return final_query
