import logging
import urllib.parse
from typing import AsyncIterator

import aiohttp

from ai.backend.common.logging import BraceStyleAdapter

from .base import (
    BaseContainerRegistry,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class GitLabRegistry(BaseContainerRegistry):
    async def fetch_repositories(self, sess: aiohttp.ClientSession) -> AsyncIterator[str]:
        name, access_token, gitlab_project = (
            self.registry_info["username"],
            self.registry_info["password"],
            self.registry_info["gitlab_project"],
        )

        projects = gitlab_project.split(",")

        for project in projects:
            encoded_project_id = urllib.parse.quote(f"{name}/{project}", safe="")
            repo_list_url = (
                f"https://gitlab.com/api/v4/projects/{encoded_project_id}/registry/repositories"
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
