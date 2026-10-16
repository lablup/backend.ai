from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.filter_specs import UUIDEqualMatchSpec
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.models.session_group.searchable_fields import SessionGroupSearchableFields
from ai.backend.manager.models.session_group.searchers import SessionGroupSearcher
from ai.backend.manager.models.specs.pagination import NoPagination

__all__ = ("GetSessionGroupAction",)


@dataclass(frozen=True)
class GetSessionGroupAction(BaseSingleEntityAction):
    """Read one session group by its id.

    A group a replica group holds is answered for as not found.
    """

    group_id: SessionGroupID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_session_group"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.group_id

    def to_searcher(self) -> SessionGroupSearcher:
        """The group named, unless a replica group holds it."""
        fields = SessionGroupSearchableFields
        return SessionGroupSearcher(
            pagination=NoPagination(),
            conditions=[
                fields.own.id.filter.equals(UUIDEqualMatchSpec(value=self.group_id, negated=False)),
                fields.linked.replica_groups.not_exists(),
            ],
        )
