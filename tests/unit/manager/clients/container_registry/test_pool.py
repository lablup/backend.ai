from __future__ import annotations

import pytest

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.manager.clients.container_registry.harbor import HarborQuotaClient
from ai.backend.manager.clients.container_registry.pool import ContainerRegistryQuotaClientPool
from ai.backend.manager.errors.container_registry import ContainerRegistryQuotaNotSupported


class TestContainerRegistryQuotaClientPool:
    def test_harbor2_gets_the_harbor_client(self) -> None:
        client = ContainerRegistryQuotaClientPool().make_client(ContainerRegistryType.HARBOR2)

        assert isinstance(client, HarborQuotaClient)

    @pytest.mark.parametrize(
        "type_",
        [
            ContainerRegistryType.DOCKER,
            ContainerRegistryType.HARBOR,
            ContainerRegistryType.GITHUB,
            ContainerRegistryType.GITLAB,
            ContainerRegistryType.ECR,
            ContainerRegistryType.ECR_PUB,
            ContainerRegistryType.LOCAL,
        ],
        ids=lambda type_: type_.value,
    )
    def test_other_types_are_rejected(self, type_: ContainerRegistryType) -> None:
        with pytest.raises(ContainerRegistryQuotaNotSupported):
            ContainerRegistryQuotaClientPool().make_client(type_)
