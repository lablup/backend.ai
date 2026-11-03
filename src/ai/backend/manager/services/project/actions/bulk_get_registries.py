from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.bulk.base import BasePartialBulkAction


@dataclass(frozen=True)
class BulkGetProjectRegistriesAction(BasePartialBulkAction):
    """Read the registries each named project is allowed on, answering an empty list for a
    project allowed on none."""

    project_ids: Sequence[ProjectID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_project_registries"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.project_ids)

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(
            self,
            project_ids=[project_id for project_id in self.project_ids if project_id in allowed],
        )
