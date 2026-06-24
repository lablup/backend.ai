import logging
import urllib.parse
from collections.abc import AsyncIterator
from typing import override

import aiohttp

from ai.backend.common.exception import ErrorDomain, ErrorOperation, PassthroughError
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.exceptions import ContainerRegistryProjectEmpty

from .base import (
    BaseContainerRegistry,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class GitLabRegistry(BaseContainerRegistry):
    @override
    async def fetch_repositories(self, sess: aiohttp.ClientSession) -> AsyncIterator[str]:
        if not self.registry_info.project:
            raise ContainerRegistryProjectEmpty(self.registry_info.type, self.registry_info.project)

        access_token = self.registry_info.password
        extra = self.registry_info.extra or {}
        api_endpoint = extra.get("api_endpoint", None)

        if api_endpoint is None:
            raise RuntimeError('"api_endpoint" is not provided for GitLab registry!')

        encoded_project_id = urllib.parse.quote(self.registry_info.project, safe="")
        repo_list_url = f"{api_endpoint}/api/v4/projects/{encoded_project_id}/registry/repositories"

        headers: dict[str, str] = {
            "Accept": "application/json",
        }
        if access_token:
            headers["PRIVATE-TOKEN"] = access_token
        page = 1

        while True:
            async with sess.get(
                repo_list_url,
                headers=headers,
                params={"per_page": 30, "page": page},
            ) as response:
                if response.status == 200:
                    data = await response.json()

                    for repo in data:
                        yield repo["path"]
                    if "next" in response.headers.get("Link", ""):
                        page += 1
                    else:
                        break
                else:
                    raise PassthroughError.from_http_status(
                        response.status,
                        domain=ErrorDomain.CONTAINER_REGISTRY,
                        operation=ErrorOperation.LIST,
                        error_message=f"Failed to fetch repositories for project "
                        f"{self.registry_info.project}! {response.status} error occurred.",
                    )
