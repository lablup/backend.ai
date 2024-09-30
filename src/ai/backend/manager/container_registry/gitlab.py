import logging
import urllib.parse
from typing import AsyncIterator, cast

import aiohttp
import sqlalchemy as sa

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.container_registry import ContainerRegistryRow

from .base import (
    BaseContainerRegistry,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class GitLabRegistry(BaseContainerRegistry):
    async def fetch_repositories(self, sess: aiohttp.ClientSession) -> AsyncIterator[str]:
        access_token = self.registry_info.password
        api_endpoint = self.registry_info.extra.get("api_endpoint", None)

        if api_endpoint is None:
            raise RuntimeError('"api_endpoint" is not provided for GitLab registry!')

        async with self.db.begin_readonly_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ContainerRegistryRow.project).where(
                    ContainerRegistryRow.registry_name == self.registry_info.registry_name
                )
            )
            projects = cast(list[str], result.scalars().all())

        for project in projects:
            encoded_project_id = urllib.parse.quote(project, safe="")
            repo_list_url = (
                f"{api_endpoint}/api/v4/projects/{encoded_project_id}/registry/repositories"
            )

            headers = {
                "Accept": "application/json",
                "PRIVATE-TOKEN": access_token,
            }
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
                        raise RuntimeError(
                            f"Failed to fetch repositories for project {project}! {response.status} error occurred."
                        )
