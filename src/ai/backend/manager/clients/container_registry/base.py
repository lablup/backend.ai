from __future__ import annotations

import abc
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


class AbstractContainerRegistryQuotaClient(abc.ABC):
    async def create_quota(
        self,
        project_info: ContainerRegistryProjectInfo,
        quota: int,
        auth_args: ContainerRegistryAuthArgs,
    ) -> None:
        raise NotImplementedError

    async def update_quota(
        self,
        project_info: ContainerRegistryProjectInfo,
        quota: int,
        auth_args: ContainerRegistryAuthArgs,
    ) -> None:
        raise NotImplementedError

    async def delete_quota(
        self, project_info: ContainerRegistryProjectInfo, auth_args: ContainerRegistryAuthArgs
    ) -> None:
        raise NotImplementedError

    async def read_quota(
        self, project_info: ContainerRegistryProjectInfo, auth_args: ContainerRegistryAuthArgs
    ) -> int:
        raise NotImplementedError
