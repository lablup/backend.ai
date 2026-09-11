from abc import ABC, abstractmethod
from dataclasses import dataclass

from ai.backend.common.data.entity.types import FieldType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.scopes import OperationScope


@dataclass
class FieldData:
    field_type: FieldType
    field_id: str


@dataclass
class BatchFieldData:
    field_type: FieldType
    field_ids: list[str]


class ActionTarget(ABC):
    @abstractmethod
    def to_rbac_element_ref(self) -> RBACElementRef:
        raise NotImplementedError


class SearchableActionTarget(ActionTarget):
    @abstractmethod
    def to_search_scope(self) -> OperationScope:
        raise NotImplementedError
