from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import aiohttp


@dataclass
class ContainerRegistryProjectInfo:
    url: str
    project: str
    ssl_verify: bool


@dataclass
class ContainerRegistryAuthArgs:
    username: str
    password: str

    def to_aiohttp_auth_args(self) -> dict[str, Any]:
        return {"auth": aiohttp.BasicAuth(self.username, self.password)}


class AbstractContainerRegistryQuotaClient(ABC):
    @abstractmethod
    async def create_quota(
        self,
        registry_info: ContainerRegistryProjectInfo,
        quota: int,
        auth_args: ContainerRegistryAuthArgs,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update_quota(
        self,
        registry_info: ContainerRegistryProjectInfo,
        quota: int,
        auth_args: ContainerRegistryAuthArgs,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete_quota(
        self, registry_info: ContainerRegistryProjectInfo, auth_args: ContainerRegistryAuthArgs
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def read_quota(
        self, registry_info: ContainerRegistryProjectInfo, auth_args: ContainerRegistryAuthArgs
    ) -> int:
        raise NotImplementedError
