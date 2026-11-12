from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.filter_specs import UUIDInMatchSpec
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.bulk.base import BasePartialBulkAction
from ai.backend.manager.models.session_group.searchable_fields import SessionGroupSearchableFields
from ai.backend.manager.models.session_group.searchers import SessionGroupSearcher
from ai.backend.manager.models.specs.pagination import NoPagination

__all__ = ("BulkGetSessionGroupsAction",)


@dataclass(frozen=True)
class BulkGetSessionGroupsAction(BasePartialBulkAction):
    """Read the session groups the caller named, answering for each id.

    A group a replica group holds answers empty, as a group that does not exist does.
    """

    ids: Sequence[SessionGroupID]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_session_groups"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(
            self,
            ids=[session_group_id for session_group_id in self.ids if session_group_id in allowed],
        )

    def to_searcher(self) -> SessionGroupSearcher:
        """The groups named, leaving out the ones a replica group holds."""
        fields = SessionGroupSearchableFields
        return SessionGroupSearcher(
            pagination=NoPagination(),
            conditions=[
                fields.own.id.filter.in_(UUIDInMatchSpec(values=list(self.ids), negated=False)),
                fields.linked.replica_groups.not_exists(),
            ],
        )
