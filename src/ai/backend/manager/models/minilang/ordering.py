from typing import (
    Mapping,
)

from lark import Lark, LarkError, Transformer
import sqlalchemy as sa

__all__ = (
    'QueryOrderParser',
)

_grammar = r"""
    ?start: expr
    expr   : [col ("," col)*]
    col    : ORDER? CNAME
    ORDER  : "+" | "-"
    %import common.CNAME
    %import common.WS
    %ignore WS
"""
_parser = Lark(
    _grammar,
    parser='lalr',
    maybe_placeholders=False,
)


class QueryOrderTransformer(Transformer):

    def __init__(self, sa_table: sa.Table, column_map: Mapping[str, str] = None) -> None:
        super().__init__()
        self._sa_table = sa_table
        self._column_map = column_map

    def _get_col(self, col_name: str) -> sa.Column:
        try:
            if self._column_map:
                col = self._sa_table.c[self._column_map[col_name]]
            else:
                col = self._sa_table.c[col_name]
            return col
        except KeyError:
            raise ValueError("Unknown/unsupported field name", col_name)

    def col(self, *args):
        children = args[0]
        if len(children) == 2:
            op = children[0].value
            col = self._get_col(children[1].value)
        else:
            op = "+"  # assume ascending if not marked
            col = self._get_col(children[0].value)
        if op == "+":
            return col.asc()
        elif op == "-":
            return col.desc()

    expr = tuple


class QueryOrderParser():

    def __init__(self, column_map: Mapping[str, str] = None) -> None:
        self._column_map = column_map
        self._parser = _parser

    def append_ordering(
        self,
        sa_query: sa.sql.Select,
        order_expr: str,
    ) -> sa.sql.Select:
        """
        Parse the given filter expression and build the where clause based on the first target table from
        the given SQLAlchemy query object.
        """
        table = sa_query.froms[0]
        try:
            ast = self._parser.parse(order_expr)
            orders = QueryOrderTransformer(table, self._column_map).transform(ast)
        except LarkError as e:
            raise ValueError(f"Query ordering parsing error: {e}")
        return sa_query.order_by(*orders)
