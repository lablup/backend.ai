import logging
from typing import AsyncIterator

import aiohttp

from ai.backend.common.logging import BraceStyleAdapter

from .base import (
    BaseContainerRegistry,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class GitHubRegistry_v2(BaseContainerRegistry):
    async def fetch_repositories(
        self,
        sess: aiohttp.ClientSession,
    ) -> AsyncIterator[str]:
        name, access_token, type_ = (
            self.registry_info["username"],
            self.registry_info["password"],
            self.registry_info["entity_type"],
        )

        base_url = f"https://api.github.com/{type_}/{name}/packages"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        page = 1

        while True:
            async with sess.get(
                base_url,
                headers=headers,
                params={"package_type": "container", "per_page": 30, "page": page},
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    for repo in data:
                        yield f"{self.registry_info["username"]}/{repo["name"]}"
                    if "next" in response.links:
                        page += 1
                    else:
                        break
                else:
                    raise RuntimeError(
                        f"Failed to fetch repositories! {response.status} error occured."
                    )
