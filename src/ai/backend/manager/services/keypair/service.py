"""
KeyPair service stub.

The actual implementation will be provided by the service-layer issue.
This stub defines the service interface used by KeyPairProcessors.
"""

from __future__ import annotations

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


class KeyPairService:
    async def create_keypair(self, action: CreateKeyPairAction) -> CreateKeyPairActionResult:
        raise NotImplementedError

    async def get_keypair(self, action: GetKeyPairAction) -> GetKeyPairActionResult:
        raise NotImplementedError

    async def search_keypairs(self, action: SearchKeyPairsAction) -> SearchKeyPairsActionResult:
        raise NotImplementedError

    async def update_keypair(self, action: UpdateKeyPairAction) -> UpdateKeyPairActionResult:
        raise NotImplementedError

    async def delete_keypair(self, action: DeleteKeyPairAction) -> DeleteKeyPairActionResult:
        raise NotImplementedError

    async def activate_keypair(self, action: ActivateKeyPairAction) -> ActivateKeyPairActionResult:
        raise NotImplementedError

    async def deactivate_keypair(
        self, action: DeactivateKeyPairAction
    ) -> DeactivateKeyPairActionResult:
        raise NotImplementedError
