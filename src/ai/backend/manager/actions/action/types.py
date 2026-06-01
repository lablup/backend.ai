from abc import ABC, abstractmethod
from dataclasses import dataclass

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.base.types import SearchScope


@dataclass
class FieldData:
    field_type: EntityType
    field_id: str


@dataclass
class BatchFieldData:
    field_type: EntityType
    field_ids: list[str]


class ActionTarget(ABC):
    @abstractmethod
    def to_rbac_element_ref(self) -> RBACElementRef:
        raise NotImplementedError


class SearchableActionTarget(ActionTarget):
    @abstractmethod
    def to_search_scope(self) -> SearchScope:
        raise NotImplementedError
