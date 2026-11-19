"""Page through the SSH keypairs of several users."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.v2.ops.base import BulkScopedSearchOpsAction
from ai.backend.manager.data.ssh_keypair.types import SSHKeypairData
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.models.ssh_keypair.row import SSHKeypairRow
from ai.backend.manager.models.ssh_keypair.scopes import UserSSHKeypairTarget
from ai.backend.manager.models.ssh_keypair.searchers import SSHKeypairSearcher


@dataclass(frozen=True)
class SearchSSHKeypairsAction(BulkScopedSearchOpsAction[SSHKeypairRow, SSHKeypairData]):
    """Page through the SSH keypairs of the users named, combined with OR."""

    user_ids: Sequence[UserID]
    searcher: SSHKeypairSearcher

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.user_ids)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return [UserSSHKeypairTarget(user_id=user_id) for user_id in self.user_ids]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_ssh_keypairs"

    @override
    def to_searcher(self) -> SSHKeypairSearcher:
        return self.searcher
