"""SSH key processor calls and DTO conversion, shared by GQL and REST v2."""

from __future__ import annotations

from collections.abc import Sequence

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.ssh_keypair import SSHKeypairID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.ssh_key.request import (
    MyUploadSSHKeyInput,
    ScopedSearchSSHKeysInput,
    SSHKeyOrderField,
)
from ai.backend.common.dto.manager.v2.ssh_key.response import SearchSSHKeysPayload, SSHKeyNode
from ai.backend.common.exception import UnreachableError
from ai.backend.common.types import SSHPublicKey
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.ssh_keypair.types import SSHKeypairData
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.ssh_keypair.row import SSHKeypairRow
from ai.backend.manager.models.ssh_keypair.scopes import UserSSHKeypairTarget
from ai.backend.manager.models.ssh_keypair.searchable_fields import SSHKeypairSearchableFields
from ai.backend.manager.models.ssh_keypair.searchers import SSHKeypairSearcher
from ai.backend.manager.services.ssh_key.actions.bulk_get import BulkGetSSHKeysAction
from ai.backend.manager.services.ssh_key.actions.get import GetSSHKeyAction
from ai.backend.manager.services.ssh_key.actions.search import ScopedSearchSSHKeypairsAction
from ai.backend.manager.services.ssh_key.actions.switch_default import (
    SwitchDefaultSSHKeyAction,
)
from ai.backend.manager.services.ssh_key.actions.upload import UploadSSHPublicKeyAction
from ai.backend.manager.services.ssh_key.processors import SSHKeyProcessors

_SSH_KEY_PAGINATION_SPEC = PaginationSpec(
    forward_order=SSHKeypairSearchableFields.own.id.order.apply(ascending=True),
    cursor_column=SSHKeypairRow.id,
)


class SSHKeyAdapter(BaseAdapter):
    _ssh_key: SSHKeyProcessors

    def __init__(self, ssh_key: SSHKeyProcessors) -> None:
        self._ssh_key = ssh_key

    async def my_upload(self, input: MyUploadSSHKeyInput) -> SSHKeyNode:
        """Upload a public key to the current user."""
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        result = await self._ssh_key.upload.run(
            UploadSSHPublicKeyAction(
                user_id=UserID(me.user_id), public_key=SSHPublicKey(input.public_key)
            )
        )
        return self._to_node(result.ssh_key)

    async def switch_default(self, ssh_key_id: SSHKeypairID) -> SSHKeyNode:
        result = await self._ssh_key.switch_default.run(
            SwitchDefaultSSHKeyAction(ssh_key_id=ssh_key_id)
        )
        return self._to_node(result.ssh_key)

    async def bulk_get_ids(
        self, ids: Sequence[SSHKeypairID]
    ) -> list[SSHKeyNode | Exception | None]:
        """Batch load SSH keys by id for DataLoader use, checked per owning user."""
        if not ids:
            return []
        return await self.batch_load_fields(
            self._ssh_key.bulk_get_ids, BulkGetSSHKeysAction(ids=ids), ids, self._to_node
        )

    async def get(self, ssh_key_id: SSHKeypairID) -> SSHKeyNode:
        """Read one SSH key; the caller needs READ on the owning user."""
        result = await self._ssh_key.get.run(GetSSHKeyAction(ssh_key_id=ssh_key_id))
        return self._to_node(result.data)

    async def scoped_search(self, input: ScopedSearchSSHKeysInput) -> SearchSSHKeysPayload:
        """Search the SSH keys of one user."""
        conditions: list[QueryCondition] = []
        if input.filter is not None and input.filter.is_default is not None:
            conditions.append(
                SSHKeypairSearchableFields.own.is_default.filter.equals(input.filter.is_default)
            )
        searcher = self._build_searcher(
            SSHKeypairSearcher,
            conditions=conditions,
            orders=[self._convert_order(o.field, o.direction) for o in input.order or []],
            pagination_spec=_SSH_KEY_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        result = await self._ssh_key.scoped_search.run(
            ScopedSearchSSHKeypairsAction(
                targets=[UserSSHKeypairTarget(user_id=UserID(input.user_id))],
                searcher=searcher,
            )
        )
        return SearchSSHKeysPayload(
            items=[self._to_node(item) for item in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    @staticmethod
    def _convert_order(field: SSHKeyOrderField, direction: OrderDirection) -> QueryOrder:
        ascending = direction == OrderDirection.ASC
        match field:
            case SSHKeyOrderField.IS_DEFAULT:
                return SSHKeypairSearchableFields.own.is_default.order.apply(ascending)

    @staticmethod
    def _to_node(data: SSHKeypairData) -> SSHKeyNode:
        return SSHKeyNode(
            id=data.id,
            field_id=data.id,
            user_id=data.user_id,
            public_key=data.public_key,
            is_default=data.is_default,
        )
