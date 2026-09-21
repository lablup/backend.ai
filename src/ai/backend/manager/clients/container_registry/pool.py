from __future__ import annotations

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.manager.clients.container_registry.base import (
    AbstractContainerRegistryQuotaClient,
)
from ai.backend.manager.clients.container_registry.harbor import HarborQuotaClient
from ai.backend.manager.errors.common import GenericBadRequest


class ContainerRegistryQuotaClientPool:
    def make_client(self, type_: ContainerRegistryType) -> AbstractContainerRegistryQuotaClient:
        match type_:
            case ContainerRegistryType.HARBOR2:
                return HarborQuotaClient()
            case _:
                raise GenericBadRequest(
                    f"{type_} does not support registry quota per project management."
                )
