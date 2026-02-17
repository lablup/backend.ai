from __future__ import annotations

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.keypair.actions import (
    ActivateKeyPairAction,
    ActivateKeyPairActionResult,
    CreateKeyPairAction,
    CreateKeyPairActionResult,
    DeactivateKeyPairAction,
    DeactivateKeyPairActionResult,
    DeleteKeyPairAction,
    DeleteKeyPairActionResult,
    GetKeyPairAction,
    GetKeyPairActionResult,
    SearchKeyPairsAction,
    SearchKeyPairsActionResult,
    UpdateKeyPairAction,
    UpdateKeyPairActionResult,
)
from ai.backend.manager.services.keypair.service import KeyPairService


class KeyPairProcessors(AbstractProcessorPackage):
    create: ActionProcessor[CreateKeyPairAction, CreateKeyPairActionResult]
    get: ActionProcessor[GetKeyPairAction, GetKeyPairActionResult]
    search: ActionProcessor[SearchKeyPairsAction, SearchKeyPairsActionResult]
    update: ActionProcessor[UpdateKeyPairAction, UpdateKeyPairActionResult]
    delete: ActionProcessor[DeleteKeyPairAction, DeleteKeyPairActionResult]
    activate: ActionProcessor[ActivateKeyPairAction, ActivateKeyPairActionResult]
    deactivate: ActionProcessor[DeactivateKeyPairAction, DeactivateKeyPairActionResult]

    def __init__(self, service: KeyPairService, action_monitors: list[ActionMonitor]) -> None:
        self.create = ActionProcessor(service.create_keypair, action_monitors)
        self.get = ActionProcessor(service.get_keypair, action_monitors)
        self.search = ActionProcessor(service.search_keypairs, action_monitors)
        self.update = ActionProcessor(service.update_keypair, action_monitors)
        self.delete = ActionProcessor(service.delete_keypair, action_monitors)
        self.activate = ActionProcessor(service.activate_keypair, action_monitors)
        self.deactivate = ActionProcessor(service.deactivate_keypair, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateKeyPairAction.spec(),
            GetKeyPairAction.spec(),
            SearchKeyPairsAction.spec(),
            UpdateKeyPairAction.spec(),
            DeleteKeyPairAction.spec(),
            ActivateKeyPairAction.spec(),
            DeactivateKeyPairAction.spec(),
        ]
