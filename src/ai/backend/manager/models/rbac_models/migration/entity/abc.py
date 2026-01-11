from abc import ABC, abstractmethod
from typing import Self, TypeVar

import sqlalchemy as sa
from sqlalchemy.engine.row import Row

from ai.backend.manager.data.permission.id import ObjectId, ScopeId

from ..enums import EntityType, OperationType


class AbstractEntityType(ABC):
    @classmethod
    @abstractmethod
    def from_row(cls, row: Row) -> Self:
        pass

    @abstractmethod
    def scopes(self) -> list[ScopeId]:
        pass

    @abstractmethod
    def entity_id(self) -> ObjectId:
        pass

    @classmethod
    @abstractmethod
    def entity_type(cls) -> EntityType:
        pass

    @classmethod
    @abstractmethod
    def operations_in_system_role(cls) -> set[OperationType]:
        pass

    @classmethod
    @abstractmethod
    def operations_in_custom_role(cls) -> set[OperationType]:
        pass

    @classmethod
    @abstractmethod
    def query_statement(cls) -> sa.sql.Select:
        pass


TEntity = TypeVar("TEntity", bound=AbstractEntityType)
