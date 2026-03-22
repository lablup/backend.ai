"""Service actions for self-service keypair operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.keypair.types import GeneratedKeyPairData
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
        return self.generated_data.access_key


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
    access_key: str
    is_active: bool

    @override
    def entity_id(self) -> str | None:
        return self.access_key

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateMyKeypairActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> str | None:
        return None


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
