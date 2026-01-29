import enum
from collections.abc import Mapping
from typing import NamedTuple

import sqlalchemy as sa
from lark import Lark, LarkError, Transformer
from lark.lexer import Token

from . import JSONFieldItem, OrderSpecItem, get_col_from_table

__all__ = (
    "ColumnMapType",
    "QueryOrderParser",
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
    parser="lalr",
    maybe_placeholders=False,
)

type ColumnMapType = Mapping[str, OrderSpecItem] | None


class OrderDirection(enum.Enum):
    ASC = "asc"
    DESC = "desc"


class OrderingItem(NamedTuple):
    column: sa.Column | sa.orm.attributes.InstrumentedAttribute | sa.sql.elements.KeyedColumnElement
    order_direction: OrderDirection


class QueryOrderTransformer(Transformer):
    def __init__(
        self, sa_table: sa.Table | sa.sql.Join | type, column_map: ColumnMapType | None = None
    ) -> None:
        super().__init__()
        self._sa_table = sa_table
        self._column_map = column_map

    def _get_col(
        self, col_name: str
    ) -> sa.Column | sa.orm.attributes.InstrumentedAttribute | sa.sql.elements.KeyedColumnElement:
        try:
            if self._column_map:
                col_value, func = self._column_map[col_name]
                match col_value:
                    case str(column):
                        matched_col = get_col_from_table(self._sa_table, column)
                    case JSONFieldItem(_col, _key):
                        _column = get_col_from_table(self._sa_table, _col)
                        matched_col = _column.op("->>")(_key)  # type: ignore[assignment]
                    case _:
                        raise ValueError("Invalid type of field name", col_name)
                col = func(matched_col) if func is not None else matched_col  # type: ignore[arg-type]
            else:
                col = get_col_from_table(self._sa_table, col_name)
            return col  # type: ignore[return-value]
        except KeyError as e:
            raise ValueError("Unknown/unsupported field name", col_name) from e

    def col(self, *args) -> OrderingItem:
        children: list[Token] = args[0]
        if len(children) == 2:
            op = children[0].value
            col = self._get_col(children[1].value)
        else:
            op = "+"  # assume ascending if not marked
            col = self._get_col(children[0].value)
        if op == "+":
            return OrderingItem(col, OrderDirection.ASC)
        if op == "-":
            return OrderingItem(col, OrderDirection.DESC)
        raise ValueError(f"Invalid operation `{op}`. Please use `+` or `-`")

    expr = tuple


class QueryOrderParser:
    def __init__(self, column_map: ColumnMapType | None = None) -> None:
        self._column_map = column_map
        self._parser = _parser

    def parse_order(
        self, table: sa.Table | sa.sql.Join | type, order_expr: str
    ) -> list[OrderingItem]:
        try:
            ast = self._parser.parse(order_expr)
            return QueryOrderTransformer(table, self._column_map).transform(ast)
        except LarkError as e:
            raise ValueError(f"Query ordering parsing error: {e}") from e

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
        # FromClause is compatible with our union type, cast for type checker
        from typing import cast

        parsed_table = cast(sa.Table | sa.sql.Join | type, table)
        orders = [
            col.asc() if direction == OrderDirection.ASC else col.desc()
            for col, direction in self.parse_order(parsed_table, order_expr)
        ]
        return sa_query.order_by(*orders)
