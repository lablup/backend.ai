from typing import (
    Any,
    Mapping,
    Union,
)

from lark import Lark, LarkError, Transformer, Tree
import sqlalchemy as sa

from . import FieldSpecItem

__all__ = (
    'FilterableSQLQuery',
    'QueryFilterParser',
)


FilterableSQLQuery = Union[sa.sql.Select, sa.sql.Update, sa.sql.Delete]

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
    parser='lalr',
    maybe_placeholders=False,
)


class QueryFilterTransformer(Transformer):

    def __init__(self, sa_table: sa.Table, fieldspec: Mapping[str, FieldSpecItem] = None) -> None:
        super().__init__()
        self._sa_table = sa_table
        self._fieldspec = fieldspec

    def string(self, s):
        (s,) = s
        # SQL-side escaping is handled by SQLAlchemy
        return s[1:-1].replace("\\\"", '"')

    def number(self, n):
        (n,) = n
        if '.' in n:
            return float(n)
        return int(n)

    array = list

    def atom(self, a):
        (a,) = a
        if a.value == "null":
            return sa.null()
        elif a.value == "true":
            return sa.true()
        elif a.value == "false":
            return sa.false()

    def _get_col(self, col_name: str) -> sa.Column:
        try:
            if self._fieldspec:
                col = self._sa_table.c[self._fieldspec[col_name][0]]
            else:
                col = self._sa_table.c[col_name]
            return col
        except KeyError:
            raise ValueError("Unknown/unsupported field name", col_name)

    def _transform_val_leaf(self, col_name: str, value: Any) -> Any:
        if self._fieldspec:
            try:
                func = self._fieldspec[col_name][1]
            except KeyError:
                raise ValueError("Unknown/unsupported field name", col_name)
            return func(value) if func is not None else value
        else:
            return value

    def _transform_val(self, col_name: str, value: Any) -> Any:
        if isinstance(value, Tree):
            val = self._transform_val(col_name, value.children[0])
        elif isinstance(value, list):
            val = [self._transform_val(col_name, v) for v in value]
        else:
            val = self._transform_val_leaf(col_name, value)
        return val

    def binary_expr(self, *args):
        children = args[0]
        col = self._get_col(children[0].value)
        op = children[1].value
        val = self._transform_val(children[0].value, children[2])
        if op == "==":
            return (col == val)
        elif op == "!=":
            return (col != val)
        elif op == ">":
            return (col > val)
        elif op == ">=":
            return (col >= val)
        elif op == "<":
            return (col < val)
        elif op == "<=":
            return (col <= val)
        elif op == "contains":
            return (col.contains(val))
        elif op == "in":
            return (col.in_(val))
        elif op == "isnot":
            return (col.isnot(val))
        elif op == "is":
            return (col.is_(val))
        elif op == "like":
            return (col.like(val))
        elif op == "ilike":
            return (col.ilike(val))
        return args

    def unary_expr(self, *args):
        children = args[0]
        op = children[0].value
        expr = children[1]
        if op in ("not", "!"):
            return (sa.not_(expr))
        return args

    def combine_expr(self, *args):
        children = args[0]
        op = children[1].value
        expr1 = children[0]
        expr2 = children[2]
        if op == "&":
            return (sa.and_(expr1, expr2))
        elif op == "|":
            return (sa.or_(expr1, expr2))
        return args

    def paren_expr(self, *args):
        children = args[0]
        return children[0]


class QueryFilterParser():

    def __init__(self, fieldspec: Mapping[str, FieldSpecItem] = None) -> None:
        self._fieldspec = fieldspec
        self._parser = _parser

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
            raise ValueError('Unsupported SQLAlchemy query object type')
        try:
            ast = self._parser.parse(filter_expr)
            where_clause = QueryFilterTransformer(table, self._fieldspec).transform(ast)
        except LarkError as e:
            raise ValueError(f"Query filter parsing error: {e}")
        return sa_query.where(where_clause)
