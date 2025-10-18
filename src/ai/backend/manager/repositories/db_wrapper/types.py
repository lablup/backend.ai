from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

from ai.backend.manager.data.permission.id import ScopeId
from ai.backend.manager.data.permission.types import EntityType

TUpdator = TypeVar("TUpdator")


class Row(ABC, Generic[TUpdator]):
    @abstractmethod
    def update_from_data(self, data: TUpdator) -> None:
        raise NotImplementedError


TRow = TypeVar("TRow", bound=Row)  # SQLAlchemy ORM model instance


class EntityRBACData(ABC):
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


TEntityRBACData = TypeVar("TEntityRBACData", bound=EntityRBACData)


@dataclass
class InsertData(Generic[TRow, TEntityRBACData]):
    row: TRow
    entity_data: TEntityRBACData


@dataclass
class UpdateData(Generic[TRow, TUpdator]):
    row: TRow
    updator: TUpdator


@dataclass
class DeleteData(Generic[TRow, TEntityRBACData]):
    row: TRow
    entity_data: TEntityRBACData
