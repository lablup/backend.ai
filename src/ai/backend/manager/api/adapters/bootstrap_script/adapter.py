"""Bootstrap script adapter bridging DTOs and Processors."""

from __future__ import annotations

from collections.abc import Sequence

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.bootstrap_script import BootstrapScript, BootstrapScriptID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.dto.manager.defs import DEFAULT_PAGE_LIMIT
from ai.backend.common.dto.manager.v2.bootstrap_script.request import (
    CreateBootstrapScriptInput,
    SearchBootstrapScriptsInput,
    UpdateBootstrapScriptInput,
)
from ai.backend.common.dto.manager.v2.bootstrap_script.response import (
    BootstrapScriptNode,
    CreateBootstrapScriptPayload,
    PurgeBootstrapScriptPayload,
    SearchBootstrapScriptsPayload,
    SwitchDefaultBootstrapScriptPayload,
    UpdateBootstrapScriptPayload,
)
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.api.adapter_options.pagination.pagination import (
    PaginationOptions,
    PaginationSpec,
)
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.bootstrap_script.types import BootstrapScriptData
from ai.backend.manager.data.dotfile.types import normalize_newlines
from ai.backend.manager.models.bootstrap_script.creators import BootstrapScriptCreator
from ai.backend.manager.models.bootstrap_script.row import BootstrapScriptRow
from ai.backend.manager.models.bootstrap_script.searchers import BootstrapScriptSearcher
from ai.backend.manager.services.user.bootstrap_script.actions.bulk_get import (
    BulkGetBootstrapScriptsAction,
)
from ai.backend.manager.services.user.bootstrap_script.actions.create import (
    CreateBootstrapScriptAction,
)
from ai.backend.manager.services.user.bootstrap_script.actions.get import GetBootstrapScriptAction
from ai.backend.manager.services.user.bootstrap_script.actions.purge import (
    PurgeBootstrapScriptAction,
)
from ai.backend.manager.services.user.bootstrap_script.actions.search import (
    SearchBootstrapScriptsAction,
)
from ai.backend.manager.services.user.bootstrap_script.actions.switch_default import (
    SwitchDefaultBootstrapScriptAction,
)
from ai.backend.manager.services.user.bootstrap_script.actions.update import (
    UpdateBootstrapScriptAction,
)
from ai.backend.manager.services.user.bootstrap_script.processors import BootstrapScriptProcessors
from ai.backend.manager.types import OptionalState

_PAGINATION_SPEC = PaginationSpec(
    forward_order=BootstrapScriptRow.created_at.asc(),
    cursor_column=BootstrapScriptRow.id,
)


def _normalize(script: str) -> BootstrapScript:
    return BootstrapScript(normalize_newlines(script).strip())


class BootstrapScriptAdapter(BaseAdapter):
    """Adapter for the bootstrap scripts set on users."""

    _bootstrap_script: BootstrapScriptProcessors

    def __init__(self, bootstrap_script: BootstrapScriptProcessors) -> None:
        self._bootstrap_script = bootstrap_script

    @staticmethod
    def _data_to_node(data: BootstrapScriptData) -> BootstrapScriptNode:
        return BootstrapScriptNode(
            id=data.id,
            field_id=data.id,
            user_id=UserID(data.entity),
            script=data.script,
            is_default=data.is_default,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )

    async def my_create(self, input: CreateBootstrapScriptInput) -> CreateBootstrapScriptPayload:
        """Add a bootstrap script to the caller. It is not the default."""
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        result = await self._bootstrap_script.create.run(
            CreateBootstrapScriptAction(
                user_id=UserID(me.user_id),
                creator=BootstrapScriptCreator(script=_normalize(input.script), is_default=False),
            )
        )
        return CreateBootstrapScriptPayload(bootstrap_script=self._data_to_node(result.data))

    async def get(self, script_id: BootstrapScriptID) -> BootstrapScriptNode:
        result = await self._bootstrap_script.get.run(GetBootstrapScriptAction(script_id=script_id))
        return self._data_to_node(result.data)

    async def batch_load_by_ids(
        self, ids: Sequence[BootstrapScriptID]
    ) -> list[BootstrapScriptNode | Exception | None]:
        """Batch load bootstrap scripts for DataLoader use, checked per owning user."""
        if not ids:
            return []
        return await self.batch_load_fields(
            self._bootstrap_script.bulk_get,
            BulkGetBootstrapScriptsAction(ids=ids),
            ids,
            self._data_to_node,
        )

    async def my_search(self, input: SearchBootstrapScriptsInput) -> SearchBootstrapScriptsPayload:
        """Page through the caller's bootstrap scripts, oldest first."""
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        return await self.user_search(UserID(me.user_id), input)

    async def user_search(
        self, user_id: UserID, input: SearchBootstrapScriptsInput
    ) -> SearchBootstrapScriptsPayload:
        """Page through one user's bootstrap scripts, oldest first."""
        limit = input.limit
        options = PaginationOptions(
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        if limit is None and not options.has_cursor:
            limit = DEFAULT_PAGE_LIMIT
        searcher = self._build_searcher(
            BootstrapScriptSearcher,
            conditions=[],
            orders=[],
            pagination_spec=_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=limit,
            offset=input.offset,
        )
        result = await self._bootstrap_script.search.run(
            SearchBootstrapScriptsAction(user_id=user_id, searcher=searcher)
        )
        return SearchBootstrapScriptsPayload(
            items=[self._data_to_node(item) for item in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def update(
        self, script_id: BootstrapScriptID, input: UpdateBootstrapScriptInput
    ) -> UpdateBootstrapScriptPayload:
        result = await self._bootstrap_script.update.run(
            UpdateBootstrapScriptAction(
                script_id=script_id,
                script=OptionalState[str].from_unset(input.script).map(_normalize),
            )
        )
        return UpdateBootstrapScriptPayload(bootstrap_script=self._data_to_node(result.data))

    async def switch_default(
        self, script_id: BootstrapScriptID
    ) -> SwitchDefaultBootstrapScriptPayload:
        result = await self._bootstrap_script.switch_default.run(
            SwitchDefaultBootstrapScriptAction(script_id=script_id)
        )
        return SwitchDefaultBootstrapScriptPayload(
            bootstrap_script=self._data_to_node(result.script)
        )

    async def purge(self, script_id: BootstrapScriptID) -> PurgeBootstrapScriptPayload:
        result = await self._bootstrap_script.purge.run(
            PurgeBootstrapScriptAction(script_id=script_id)
        )
        return PurgeBootstrapScriptPayload(id=result.data.id)
