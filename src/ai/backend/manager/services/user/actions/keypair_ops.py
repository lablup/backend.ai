"""Service actions for keypair operations (self-service and admin)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.data.keypair.types import GeneratedKeyPairData, KeyPairCreator, KeyPairData
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.repositories.base.querier import BatchQuerier
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.keypair.types import UserKeypairSearchScope
from ai.backend.manager.services.user.actions.base import UserAction


@dataclass
class IssueMyKeypairAction(UserAction):
    """Issue a new keypair for the current user."""

    user_uuid: UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.user_uuid)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class IssueMyKeypairActionResult(BaseActionResult):
    generated_data: GeneratedKeyPairData

    @override
    def entity_id(self) -> str | None:
        return str(self.generated_data.keypair.access_key)


@dataclass
class RevokeMyKeypairAction(UserAction):
    """Revoke a keypair owned by the current user."""

    user_uuid: UUID
    access_key: str

    @override
    def entity_id(self) -> str | None:
        return self.access_key

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class RevokeMyKeypairActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class UpdateMyKeypairAction(UserAction):
    """Update a keypair owned by the current user (e.g. toggle active state)."""

    user_uuid: UUID
    updater: Updater[KeyPairRow]

    @override
    def entity_id(self) -> str | None:
        return str(self.updater.pk_value)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateMyKeypairActionResult(BaseActionResult):
    keypair: KeyPairData

    @override
    def entity_id(self) -> str | None:
        return str(self.keypair.access_key)


@dataclass
class SwitchMyMainAccessKeyAction(UserAction):
    """Switch the main access key for the current user."""

    user_uuid: UUID
    access_key: str

    @override
    def entity_id(self) -> str | None:
        return self.access_key

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class SwitchMyMainAccessKeyActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class SearchMyKeypairsAction(UserAction):
    """Search keypairs owned by the current user."""

    scope: UserKeypairSearchScope
    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchMyKeypairsActionResult(BaseActionResult):
    result: SearchResult[KeyPairData]

    @override
    def entity_id(self) -> str | None:
        return None


# ------------------------------------------------------------------ admin keypair actions


@dataclass
class AdminCreateKeypairAction(UserAction):
    """Admin action to create a keypair for a specific user."""

    user_id: UUID
    creator: KeyPairCreator

    @override
    def entity_id(self) -> str | None:
        return str(self.user_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class AdminCreateKeypairActionResult(BaseActionResult):
    generated_data: GeneratedKeyPairData

    @override
    def entity_id(self) -> str | None:
        return str(self.generated_data.keypair.access_key)


@dataclass
class AdminUpdateKeypairAction(UserAction):
    """Admin action to update any keypair."""

    updater: Updater[KeyPairRow]

    @override
    def entity_id(self) -> str | None:
        return str(self.updater.pk_value)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class AdminUpdateKeypairActionResult(BaseActionResult):
    keypair: KeyPairData

    @override
    def entity_id(self) -> str | None:
        return str(self.keypair.access_key)


@dataclass
class AdminDeleteKeypairAction(UserAction):
    """Admin action to delete any keypair."""

    access_key: str

    @override
    def entity_id(self) -> str | None:
        return self.access_key

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class AdminDeleteKeypairActionResult(BaseActionResult):
    access_key: str

    @override
    def entity_id(self) -> str | None:
        return self.access_key


@dataclass
class AdminSearchKeypairsAction(UserAction):
    """Admin action to search all keypairs without user scope."""

    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class AdminSearchKeypairsActionResult(BaseActionResult):
    result: SearchResult[KeyPairData]

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class AdminGetKeypairAction(UserAction):
    """Admin action to get a single keypair by access key."""

    access_key: str

    @override
    def entity_id(self) -> str | None:
        return self.access_key

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class AdminGetKeypairActionResult(BaseActionResult):
    keypair: KeyPairData

    @override
    def entity_id(self) -> str | None:
        return str(self.keypair.access_key)
