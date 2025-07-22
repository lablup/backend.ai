import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TypeVar


@dataclass
class BaseQueryParams:
    user_id: uuid.UUID
    entity_type: str
    operation_type: str


@dataclass
class SingleEntityQueryParams(BaseQueryParams):
    entity_id: str


@dataclass
class ScopeQueryParams(BaseQueryParams):
    scope_type: str
    scope_id: str


@dataclass
class MultipleEntityQueryParams(BaseQueryParams):
    entity_ids: Iterable[str]


TQueryParams = TypeVar("TQueryParams", bound=BaseQueryParams)
