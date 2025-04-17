import enum
from dataclasses import dataclass, field
from typing import Callable, Optional, Protocol, Self

import sqlalchemy as sa

type QuerySingleCondition = sa.sql.expression.BinaryExpression

type QueryOptionCallable = Callable[[sa.sql.Select], sa.sql.Select]
type QueryOption = Callable[..., Callable[[sa.sql.Select], sa.sql.Select]]


class ConditionMerger(enum.Enum):
    AND = "AND"
    OR = "OR"

    @property
    def sql_operator(self) -> Callable:
        match self:
            case ConditionMerger.AND:
                return sa.and_
            case ConditionMerger.OR:
                return sa.or_


@dataclass
class QueryCondition:
    condition: Optional[QuerySingleCondition] = None

    @classmethod
    def multiple(cls, operator: ConditionMerger, conditions: list[Self]) -> Self:
        sql_conditions = [cond.condition for cond in conditions if cond.condition is not None]
        if not sql_conditions:
            return cls()
        if len(sql_conditions) == 1:
            return cls(sql_conditions[0])
        return cls(operator.sql_operator(*sql_conditions))

    @classmethod
    def single(cls, condition: QuerySingleCondition) -> Self:
        return cls(condition)


@dataclass
class QueryArgument:
    _condition: QueryCondition
    options: list[QueryOption] = field(default_factory=list)

    @property
    def condition(self) -> Optional[QuerySingleCondition]:
        return self._condition.condition if self._condition.condition is not None else None


class _LoadableField(Protocol):
    def __call__(self, *args, **kwargs) -> Callable:
        pass


class _JoinableField(Protocol):
    def __call__(self, *args, **kwargs) -> sa.orm.attributes.InstrumentedAttribute:
        pass


def load_related_field(field: _LoadableField) -> QueryOptionCallable:
    return lambda stmt: stmt.options(field())


def join_by_related_field(field: _JoinableField) -> QueryOptionCallable:
    return lambda stmt: stmt.join(field())
