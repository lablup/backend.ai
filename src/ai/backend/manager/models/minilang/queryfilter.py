import enum
from typing import Any, Callable, Mapping, Type, TypeAlias, TypeVar, Union

import sqlalchemy as sa
from lark import Lark, LarkError, Transformer, Tree
from lark.lexer import Token

from . import ArrayFieldItem, FieldSpecItem, JSONFieldItem, get_col_from_table

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
T_Enum = TypeVar("T_Enum", bound=enum.Enum)


def enum_field_getter(enum_cls: Type[T_Enum]) -> Callable[[str], T_Enum]:
    def get_enum(value: str) -> T_Enum:
        for enum_name in (value, value.upper()):
            try:
                return enum_cls[enum_name]
            except KeyError:
                continue
        else:
            enum_names = ", ".join([e.name for e in enum_cls])
            raise ValueError(f"expected one of `{enum_names}` or lower names; got `{value}`")

    return get_enum


class QueryFilterTransformer(Transformer):
    def __init__(self, sa_table: sa.Table, fieldspec: FieldSpecType = None) -> None:
        super().__init__()
        self._sa_table = sa_table
        self._fieldspec = fieldspec

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

    def binary_expr(self, *args) -> sa.sql.elements.BinaryExpression:
        children: list[Token] = args[0]
        col_name = children[0].value
        op = children[1].value
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
        if op == "&":
            return sa.and_(expr1, expr2)
        elif op == "|":
            return sa.or_(expr1, expr2)
        return args

    def paren_expr(self, *args):
        children = args[0]
        return children[0]


class QueryFilterParser:
    def __init__(self, fieldspec: FieldSpecType = None) -> None:
        self._fieldspec = fieldspec
        self._parser = _parser

    def parse_filter(
        self,
        table,
        filter_expr: str,
    ) -> WhereClauseType:
        try:
            ast = self._parser.parse(filter_expr)
            where_clause = QueryFilterTransformer(table, self._fieldspec).transform(ast)
        except LarkError as e:
            raise ValueError(f"Query filter parsing error: {e}")
        return where_clause

    def append_filter(
        self,
        sa_query: FilterableSQLQuery,
        filter_expr: str,
    ) -> FilterableSQLQuery:
        """
        Parse the given filter expression and build the where clause based on the first target table from
        the given SQLAlchemy query object.
        """
        if isinstance(sa_query, sa.sql.Select):
            table = sa_query.froms[0]
        elif isinstance(sa_query, sa.sql.Delete):
            table = sa_query.table
        elif isinstance(sa_query, sa.sql.Update):
            table = sa_query.table
        else:
            raise ValueError("Unsupported SQLAlchemy query object type")
        where_clause = self.parse_filter(table, filter_expr)
        final_query = sa_query.where(where_clause)
        assert final_query is not None
        return final_query
