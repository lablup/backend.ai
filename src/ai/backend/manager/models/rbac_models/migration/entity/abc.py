from abc import ABC, abstractmethod
from collections.abc import Generator
from typing import Generic, Self, TypeVar

import sqlalchemy as sa
from sqlalchemy.engine import Connection
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


class EntityQuerier(Generic[TEntity]):
    def __init__(self, entity_type: type[TEntity]) -> None:
        self._entity_type = entity_type

    def query_entities(
        self,
        db_conn: Connection,
    ) -> Generator[list[TEntity], None, None]:
        offset = 0
        limit = 100

        while True:
            stmt = self._entity_type.query_statement().offset(offset).limit(limit)
            result = db_conn.execute(stmt)
            rows = result.all()
            if not rows:
                break

            offset += limit
            yield [self._entity_type.from_row(entity_row) for entity_row in rows]
