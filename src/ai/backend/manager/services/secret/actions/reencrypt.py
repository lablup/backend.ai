from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.secret import SECRET_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.data.secret.types import SecretReencryptProgress


@dataclass(frozen=True)
class ReencryptSecretsAction(BaseGlobalAction):
    """Encrypt every stored secret again through the configured write provider."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SECRET_ENTITY_TYPE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "reencrypt_secrets"


@dataclass(frozen=True)
class ReencryptSecretsActionResult:
    progress: SecretReencryptProgress
