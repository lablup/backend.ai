from __future__ import annotations

import abc
import logging
from dataclasses import dataclass
from typing import TypedDict, override

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.client.container_registry.harbor import (
    AbstractPerProjectRegistryQuotaClient,
    PerProjectHarborQuotaClient,
)
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.models.rbac import ProjectScope
from ai.backend.manager.service.container_registry.base import (
    ContainerRegistryRowInfo,
    PerProjectRegistryQuotaRepository,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class HarborProjectInfo:
    url: str
    project: str
    ssl_verify: bool


class HarborAuthArgs(TypedDict):
    username: str
    password: str


class HarborProjectQuotaInfo(TypedDict):
    previous_quota: int
    quota_id: int


class AbstractPerProjectContainerRegistryQuotaService(abc.ABC):
    async def create_quota(
        self,
        scope_id: ProjectScope,
        quota: int,
    ) -> None:
        raise NotImplementedError

    async def update_quota(
        self,
        scope_id: ProjectScope,
        quota: int,
    ) -> None:
        raise NotImplementedError

    async def delete_quota(
        self,
        scope_id: ProjectScope,
    ) -> None:
        raise NotImplementedError

    async def read_quota(
        self,
        scope_id: ProjectScope,
    ) -> int:
        raise NotImplementedError


class PerProjectContainerRegistryQuotaClientPool(abc.ABC):
    def make_client(self, type_: ContainerRegistryType) -> AbstractPerProjectRegistryQuotaClient:
        match type_:
            case ContainerRegistryType.HARBOR2:
                return PerProjectHarborQuotaClient()
            case _:
                raise GenericBadRequest(
                    f"{type_} does not support registry quota per project management."
                )


class PerProjectContainerRegistryQuotaService(AbstractPerProjectContainerRegistryQuotaService):
    _repository: PerProjectRegistryQuotaRepository
    _client_pool: PerProjectContainerRegistryQuotaClientPool

    def __init__(
        self,
        repository: PerProjectRegistryQuotaRepository,
        client_pool: PerProjectContainerRegistryQuotaClientPool,
    ):
        self._repository = repository
        self._client_pool = client_pool

    def _registry_row_to_harbor_project_info(
        self, registry_info: ContainerRegistryRowInfo
    ) -> HarborProjectInfo:
        return HarborProjectInfo(
            url=registry_info.url,
            project=registry_info.project,
            ssl_verify=registry_info.ssl_verify,
        )

    @override
    async def create_quota(
        self,
        scope_id: ProjectScope,
        quota: int,
    ) -> None:
        registry_info = await self._repository.fetch_container_registry_row(scope_id)
        client = self._client_pool.make_client(registry_info.type)
        project_info = self._registry_row_to_harbor_project_info(registry_info)
        credential = HarborAuthArgs(
            username=registry_info.username, password=registry_info.password
        )
        await client.create_quota(project_info, quota, credential)

    @override
    async def update_quota(
        self,
        scope_id: ProjectScope,
        quota: int,
    ) -> None:
        registry_info = await self._repository.fetch_container_registry_row(scope_id)
        client = self._client_pool.make_client(registry_info.type)
        project_info = self._registry_row_to_harbor_project_info(registry_info)
        credential = HarborAuthArgs(
            username=registry_info.username, password=registry_info.password
        )
        await client.update_quota(project_info, quota, credential)

    @override
    async def delete_quota(
        self,
        scope_id: ProjectScope,
    ) -> None:
        registry_info = await self._repository.fetch_container_registry_row(scope_id)
        client = self._client_pool.make_client(registry_info.type)
        project_info = self._registry_row_to_harbor_project_info(registry_info)
        credential = HarborAuthArgs(
            username=registry_info.username, password=registry_info.password
        )
        await client.delete_quota(project_info, credential)

    @override
    async def read_quota(self, scope_id: ProjectScope) -> int:
        registry_info = await self._repository.fetch_container_registry_row(scope_id)
        client = self._client_pool.make_client(registry_info.type)
        project_info = self._registry_row_to_harbor_project_info(registry_info)
        credential = HarborAuthArgs(
            username=registry_info.username, password=registry_info.password
        )
        return await client.read_quota(project_info, credential)
