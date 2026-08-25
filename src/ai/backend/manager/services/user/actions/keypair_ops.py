"""Service actions for keypair operations (self-service and admin).

A keypair row belongs to the user that owns it, so every operation here is answered
for by that user. A request naming a keypair by its access key resolves the owner
first, through the key owner lookup.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.entity.keypair import KeyPairID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, ScopeRef
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE, USER_SCOPE_TYPE, UserID
from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.field.base import BaseSingleFieldAction
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.ops.base import BulkGetOwnedFieldOpsAction
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.data.keypair.types import GeneratedKeyPairData, KeyPairCreator, KeyPairData
from ai.backend.manager.models.keypair.queriers import DefaultKeypairQuerier
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.keypair.scopes import UserKeypairOperationScope
from ai.backend.manager.models.keypair.updaters import KeypairUpdater
from ai.backend.manager.repositories.base.querier import BatchQuerier
from ai.backend.manager.services.user.actions.lookup_keypair_owner import LookupKeypairOwnerAction
from ai.backend.manager.types import OptionalState


@dataclass(frozen=True)
class _KeypairOfUserAction(BaseSingleEntityAction):
    """Base for a keypair write answered for by its owning user."""

    user_id: UserID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.user_id


@dataclass(frozen=True)
class IssueMyKeypairAction(_KeypairOfUserAction):
    """Issue a new keypair for a user."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "issue_keypair"


@dataclass(frozen=True)
class IssueMyKeypairActionResult:
    generated_data: GeneratedKeyPairData


@dataclass(frozen=True)
class _KeypairFieldAction(BaseSingleFieldAction[KeyPairID, UserID]):
    """Base for an operation on one keypair, answered for by the user owning it."""

    keypair_id: KeyPairID

    @override
    def to_owner_lookup_action(self) -> LookupKeypairOwnerAction:
        return LookupKeypairOwnerAction(keypair_id=self.keypair_id)


@dataclass(frozen=True)
class GetKeypairAction(_KeypairFieldAction):
    """Read one keypair."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_keypair"


@dataclass(frozen=True)
class GetKeypairActionResult:
    keypair: KeyPairData


@dataclass(frozen=True)
class UpdateKeypairAction(_KeypairFieldAction):
    """Edit one keypair."""

    is_active: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    is_admin: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    resource_policy: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    rate_limit: OptionalState[int] = field(default_factory=OptionalState[int].nop)

    def to_updater(self) -> KeypairUpdater:
        return KeypairUpdater(
            keypair_id=self.keypair_id,
            is_active=self.is_active,
            is_admin=self.is_admin,
            resource_policy=self.resource_policy,
            rate_limit=self.rate_limit,
        )

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_keypair"


@dataclass(frozen=True)
class UpdateKeypairActionResult:
    keypair: KeyPairData


@dataclass(frozen=True)
class PurgeKeypairAction(_KeypairFieldAction):
    """Remove one keypair. The row leaves the table."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_keypair"


@dataclass(frozen=True)
class PurgeKeypairActionResult:
    keypair: KeyPairData


@dataclass(frozen=True)
class SwitchDefaultAccessKeyAction(_KeypairOfUserAction):
    """Move the default marker among a user\'s keypairs onto one access key."""

    access_key: AccessKey

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "switch_default_access_key"


@dataclass(frozen=True)
class SwitchDefaultAccessKeyActionResult:
    success: bool


@dataclass(frozen=True)
class SearchMyKeypairsAction(BaseScopeAction):
    """Page through the keypairs a user owns."""

    user_id: UserID
    querier: BatchQuerier

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_ENTITY_TYPE

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=self.user_id),)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_keypairs"

    def scope(self) -> UserKeypairOperationScope:
        return UserKeypairOperationScope(user_uuid=self.user_id)


@dataclass(frozen=True)
class SearchMyKeypairsActionResult(BaseScopeActionResult):
    result: SearchResult[KeyPairData]

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return ()


@dataclass(frozen=True)
class GetDefaultKeypairsAction(BulkGetOwnedFieldOpsAction[UserID, KeyPairRow, KeyPairData]):
    """Read the keypair each named user authorizes with."""

    user_ids: Sequence[UserID]

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return self.user_ids

    @override
    def owner_ids(self) -> Sequence[UserID]:
        return self.user_ids

    @override
    def to_querier(self) -> DefaultKeypairQuerier:
        return DefaultKeypairQuerier()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_default_keypairs"


@dataclass(frozen=True)
class AdminCreateKeypairAction(_KeypairOfUserAction):
    """Issue a keypair for a named user."""

    creator: KeyPairCreator

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "admin_create_keypair"


@dataclass(frozen=True)
class AdminCreateKeypairActionResult:
    generated_data: GeneratedKeyPairData


@dataclass(frozen=True)
class AdminSearchKeypairsAction(BaseGlobalAction):
    """Read keypairs across every user."""

    querier: BatchQuerier

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_ENTITY_TYPE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_keypairs"


@dataclass(frozen=True)
class AdminSearchKeypairsActionResult:
    result: SearchResult[KeyPairData]


@dataclass(frozen=True)
class AdminRegisterSSHKeypairAction(_KeypairOfUserAction):
    """Overwrite the SSH keypair a keypair row carries."""

    access_key: str
    ssh_public_key: str
    ssh_private_key: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "admin_register_ssh_keypair"


@dataclass(frozen=True)
class AdminRegisterSSHKeypairActionResult:
    access_key: str


@dataclass(frozen=True)
class AdminDeleteSSHKeypairAction(_KeypairOfUserAction):
    """Clear the SSH keypair a keypair row carries."""

    access_key: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "admin_delete_ssh_keypair"


@dataclass(frozen=True)
class AdminDeleteSSHKeypairActionResult:
    access_key: str


@dataclass(frozen=True)
class AdminGetSSHKeypairAction(_KeypairOfUserAction):
    """Read the SSH public key a keypair row carries."""

    access_key: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "admin_get_ssh_keypair"


@dataclass(frozen=True)
class AdminGetSSHKeypairActionResult:
    access_key: str
    ssh_public_key: str | None
