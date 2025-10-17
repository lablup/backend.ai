from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

from ai.backend.manager.data.permission.id import ScopeId
from ai.backend.manager.data.permission.types import EntityType


class BaseEntityData(ABC):
    @abstractmethod
    def entity_id(self) -> str:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def entity_type(cls) -> EntityType:
        raise NotImplementedError

    @abstractmethod
    def scope_id(self) -> ScopeId:
        raise NotImplementedError


TBaseEntityData = TypeVar("TBaseEntityData", bound=BaseEntityData)
TRow = TypeVar("TRow")  # SQLAlchemy ORM model instance


@dataclass
class InsertData(Generic[TRow, TBaseEntityData]):
    row: TRow
    entity_data: TBaseEntityData


TUpdator = TypeVar("TUpdator", contravariant=True)


class Updatable(Protocol[TUpdator]):
    def update_from_data(self, data: TUpdator) -> None: ...


@dataclass
class DeleteData(Generic[TRow, TBaseEntityData]):
    row: TRow
    entity_data: TBaseEntityData
