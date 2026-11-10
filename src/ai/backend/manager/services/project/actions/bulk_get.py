from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.models.project.queriers import BulkProjectQuerier
from ai.backend.manager.models.project.row import ProjectRow


@dataclass
class BulkGetProjectsAction(PartialBulkGetEntityOpsAction[ProjectRow, ProjectData]):
    """Read the projects the caller named, answering for each id."""

    ids: Sequence[ProjectID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_projects"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkProjectQuerier:
        return BulkProjectQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])
