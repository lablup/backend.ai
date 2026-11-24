"""Bootstrap script processor calls with the v2 DTOs."""

from __future__ import annotations

from collections.abc import Sequence

from ai.backend.common.data.entity.bootstrap_script import BootstrapScript, BootstrapScriptID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.dto.manager.v2.bootstrap_script.request import (
    AddBootstrapScriptRevisionInput,
    BootstrapScriptFilter,
    BootstrapScriptOrder,
    CreateBootstrapScriptInput,
    PurgeBootstrapScriptInput,
    ScopedSearchBootstrapScriptsInput,
    SwitchDefaultBootstrapScriptInput,
)
from ai.backend.common.dto.manager.v2.bootstrap_script.response import (
    AddBootstrapScriptRevisionPayload,
    BootstrapScriptNode,
    BootstrapScriptRevisionNode,
    CreateBootstrapScriptPayload,
    GetBootstrapScriptPayload,
    PurgeBootstrapScriptPayload,
    SearchBootstrapScriptsPayload,
    SwitchDefaultBootstrapScriptPayload,
)
from ai.backend.common.dto.manager.v2.bootstrap_script.types import BootstrapScriptOrderField
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.bootstrap_script.types import (
    BootstrapScriptData,
    BootstrapScriptRevisionData,
)
from ai.backend.manager.data.dotfile.types import normalize_newlines
from ai.backend.manager.models.bootstrap_script.row import BootstrapScriptRow
from ai.backend.manager.models.bootstrap_script.searchable_fields import (
    BootstrapScriptSearchableFields,
)
from ai.backend.manager.models.bootstrap_script.searchers import BootstrapScriptSearcher
from ai.backend.manager.models.bootstrap_script_revision.creators import (
    BootstrapScriptRevisionCreator,
)
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import (
    combine_conditions_and,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.services.user.bootstrap_script.actions.add_revision import (
    AddBootstrapScriptRevisionAction,
)
from ai.backend.manager.services.user.bootstrap_script.actions.bulk_get import (
    BulkGetBootstrapScriptsAction,
)
from ai.backend.manager.services.user.bootstrap_script.actions.bulk_get_current_revisions import (
    BulkGetCurrentBootstrapScriptRevisionsAction,
)
from ai.backend.manager.services.user.bootstrap_script.actions.create import (
    CreateBootstrapScriptAction,
)
from ai.backend.manager.services.user.bootstrap_script.actions.get import GetBootstrapScriptAction
from ai.backend.manager.services.user.bootstrap_script.actions.purge import (
    PurgeBootstrapScriptAction,
)
from ai.backend.manager.services.user.bootstrap_script.actions.scoped_search import (
    ScopedSearchBootstrapScriptsAction,
)
from ai.backend.manager.services.user.bootstrap_script.actions.switch_default import (
    SwitchDefaultBootstrapScriptAction,
)
from ai.backend.manager.services.user.bootstrap_script.processors import BootstrapScriptProcessors

__all__ = ("BootstrapScriptAdapter",)

_BOOTSTRAP_SCRIPT_PAGINATION_SPEC = PaginationSpec(
    forward_order=BootstrapScriptSearchableFields.own.created_at.order.apply(ascending=False),
    cursor_column=BootstrapScriptRow.id,
)


class BootstrapScriptAdapter(BaseAdapter):
    """Adapter for adding, revising, reading and removing the bootstrap scripts of users."""

    _bootstrap_script: BootstrapScriptProcessors

    def __init__(self, bootstrap_script: BootstrapScriptProcessors) -> None:
        self._bootstrap_script = bootstrap_script

    async def bulk_get_ids(
        self, ids: Sequence[BootstrapScriptID]
    ) -> list[BootstrapScriptNode | Exception | None]:
        """Batch load scripts by id for DataLoader use."""
        if not ids:
            return []
        return await self.batch_load_fields(
            self._bootstrap_script.bulk_get_ids,
            BulkGetBootstrapScriptsAction(ids=list(ids)),
            ids,
            self._to_node,
        )

    async def bulk_get_current_revisions(
        self, script_ids: Sequence[BootstrapScriptID]
    ) -> list[BootstrapScriptRevisionNode | Exception | None]:
        """Batch load the latest revision of each script for DataLoader use."""
        if not script_ids:
            return []
        return await self.batch_load_fields(
            self._bootstrap_script.bulk_get_current_revisions,
            BulkGetCurrentBootstrapScriptRevisionsAction(script_ids=list(script_ids)),
            script_ids,
            self._to_revision_node,
        )

    async def get(self, script_id: BootstrapScriptID) -> GetBootstrapScriptPayload:
        result = await self._bootstrap_script.get.run(GetBootstrapScriptAction(script_id=script_id))
        return GetBootstrapScriptPayload(bootstrap_script=self._to_node(result.data))

    async def create(
        self, input: CreateBootstrapScriptInput, creator_id: UserID
    ) -> CreateBootstrapScriptPayload:
        """Add a script that is not the user's default, with its first revision."""
        result = await self._bootstrap_script.create.run(
            CreateBootstrapScriptAction(
                user_id=UserID(input.user_id),
                script=self._normalize(input.script),
                creator_id=creator_id,
            )
        )
        return CreateBootstrapScriptPayload(revision=self._to_revision_node(result.revision))

    async def add_revision(
        self, input: AddBootstrapScriptRevisionInput, creator_id: UserID
    ) -> AddBootstrapScriptRevisionPayload:
        """Append the next revision; it becomes the script's content."""
        result = await self._bootstrap_script.add_revision.run(
            AddBootstrapScriptRevisionAction(
                creator=BootstrapScriptRevisionCreator(
                    script_id=input.id,
                    script=self._normalize(input.script),
                    creator_id=creator_id,
                )
            )
        )
        return AddBootstrapScriptRevisionPayload(revision=self._to_revision_node(result.revision))

    async def switch_default(
        self, input: SwitchDefaultBootstrapScriptInput
    ) -> SwitchDefaultBootstrapScriptPayload:
        """Make a script the user's default; the previous default stops being one."""
        result = await self._bootstrap_script.switch_default.run(
            SwitchDefaultBootstrapScriptAction(user_id=UserID(input.user_id), script_id=input.id)
        )
        return SwitchDefaultBootstrapScriptPayload(bootstrap_script=self._to_node(result.script))

    async def purge(self, input: PurgeBootstrapScriptInput) -> PurgeBootstrapScriptPayload:
        """Remove a script that is not the user's default; the default is refused."""
        await self._bootstrap_script.purge.run(PurgeBootstrapScriptAction(script_id=input.id))
        return PurgeBootstrapScriptPayload(field_id=input.id)

    async def scoped_search(
        self, input: ScopedSearchBootstrapScriptsInput
    ) -> SearchBootstrapScriptsPayload:
        """Search the scripts of the named users, combined with OR."""
        searcher = self._build_searcher(
            BootstrapScriptSearcher,
            conditions=self._convert_filter(input.filter) if input.filter else [],
            orders=[self._convert_order(o) for o in input.order] if input.order else [],
            pagination_spec=_BOOTSTRAP_SCRIPT_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        result = await self._bootstrap_script.scoped_search.run(
            ScopedSearchBootstrapScriptsAction(
                user_ids=[UserID(entry.value) for entry in input.scope.user], searcher=searcher
            )
        )
        return SearchBootstrapScriptsPayload(
            items=[self._to_node(item) for item in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    def _convert_filter(self, filter: BootstrapScriptFilter) -> list[QueryCondition]:
        fields = BootstrapScriptSearchableFields.own
        conditions = [
            *self.apply_uuid_filter(filter.field_id, fields.field_id.filter),
            *self.apply_datetime_filter(filter.created_at, fields.created_at.filter),
        ]
        if filter.is_default is not None:
            is_default = BootstrapScriptSearchableFields.nested.user_default.correlation.exists()
            conditions.append(is_default if filter.is_default else negate_conditions([is_default]))
        if filter.AND:
            for sub_filter in filter.AND:
                conditions.extend(self._convert_filter(sub_filter))
        if filter.OR:
            or_sub_conditions: list[QueryCondition] = []
            for sub_filter in filter.OR:
                sub_conditions = self._convert_filter(sub_filter)
                if sub_conditions:
                    or_sub_conditions.append(combine_conditions_and(sub_conditions))
            if or_sub_conditions:
                conditions.append(combine_conditions_or(or_sub_conditions))
        if filter.NOT:
            for sub_filter in filter.NOT:
                sub_conditions = self._convert_filter(sub_filter)
                if sub_conditions:
                    conditions.append(negate_conditions(sub_conditions))
        return conditions

    @staticmethod
    def _convert_order(order: BootstrapScriptOrder) -> QueryOrder:
        fields = BootstrapScriptSearchableFields.own
        ascending = order.direction == OrderDirection.ASC
        match order.field:
            case BootstrapScriptOrderField.CREATED_AT:
                return fields.created_at.order.apply(ascending)

    @staticmethod
    def _normalize(script: str) -> BootstrapScript:
        return BootstrapScript(normalize_newlines(script).strip())

    @staticmethod
    def _to_node(data: BootstrapScriptData) -> BootstrapScriptNode:
        return BootstrapScriptNode(
            id=data.id,
            field_id=data.id,
            user_id=data.entity,
            created_at=data.created_at,
        )

    @staticmethod
    def _to_revision_node(data: BootstrapScriptRevisionData) -> BootstrapScriptRevisionNode:
        return BootstrapScriptRevisionNode(
            id=data.id,
            field_id=data.id,
            script_id=data.script_id,
            revision_number=data.revision_number,
            script=data.script,
            creator_id=data.creator_id,
            created_at=data.created_at,
        )
