from __future__ import annotations

from typing import Any

from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.services.secret.actions.reencrypt import (
    ReencryptSecretsAction,
    ReencryptSecretsActionResult,
)
from ai.backend.manager.services.secret.actions.status import (
    GetSecretStatusAction,
    GetSecretStatusActionResult,
)
from ai.backend.manager.services.secret.service import SecretService


class SecretProcessors:
    """The stored secrets of every encrypted column, which no single entity owns, so
    both operations are global."""

    reencrypt: GlobalActionProcessor[ReencryptSecretsAction, ReencryptSecretsActionResult]
    get_status: GlobalActionProcessor[GetSecretStatusAction, GetSecretStatusActionResult]

    def __init__(self, group: ProcessorGroup[Any], service: SecretService) -> None:
        self.reencrypt = group.global_scope(ReencryptSecretsAction, service.reencrypt)
        self.get_status = group.global_scope(GetSecretStatusAction, service.get_status)
