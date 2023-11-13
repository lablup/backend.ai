import json
import logging
from typing import AsyncIterator, Optional, cast

import aiohttp
import typing_extensions
import yarl

from ai.backend.common.docker import login as registry_login
from ai.backend.common.logging import BraceStyleAdapter

from .base import BaseContainerRegistry

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class DockerHubRegistry(BaseContainerRegistry):
    @typing_extensions.deprecated(
        "Rescanning a whole Docker Hub account is disabled due to the API rate limit."
    )
    async def fetch_repositories(
        self,
        sess: aiohttp.ClientSession,
    ) -> AsyncIterator[str]:
        # We need some special treatment for the Docker Hub.
        raise DeprecationWarning(
            "Rescanning a whole Docker Hub account is disabled due to the API rate limit."
        )
        yield ""  # dead code to ensure the type of method

    async def fetch_repositories_legacy(
        self,
        sess: aiohttp.ClientSession,
    ) -> AsyncIterator[str]:
        params = {"page_size": "30"}
        username = self.registry_info["username"]
        hub_url = yarl.URL("https://hub.docker.com")
        repo_list_url: Optional[yarl.URL]
        repo_list_url = hub_url / f"v2/repositories/{username}/"
        while repo_list_url is not None:
            async with sess.get(repo_list_url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for item in data["results"]:
                        # skip legacy images
                        if item["name"].startswith("kernel-"):
                            continue
                        yield f"{username}/{item['name']}"
                else:
                    log.error(
                        "Failed to fetch repository list from {0} (status={1})",
                        repo_list_url,
                        resp.status,
                    )
                    break
            repo_list_url = None
            next_page_link = data.get("next", None)
            if next_page_link:
                next_page_url = yarl.URL(next_page_link)
                repo_list_url = hub_url.with_path(next_page_url.path).with_query(
                    next_page_url.query
                )


class DockerRegistry_v2(BaseContainerRegistry):
    async def fetch_repositories(
        self,
        sess: aiohttp.ClientSession,
    ) -> AsyncIterator[str]:
        # The credential should have the catalog search privilege.
        rqst_args = await registry_login(
            sess,
            self.registry_url,
            self.credentials,
            "registry:catalog:*",
        )
        catalog_url: Optional[yarl.URL]
        catalog_url = (self.registry_url / "v2/_catalog").with_query(
            {"n": "30"},
        )
        while catalog_url is not None:
            async with sess.get(catalog_url, **rqst_args) as resp:
                if resp.status == 200:
                    data = json.loads(await resp.read())
                    for item in data["repositories"]:
                        yield item
                    log.debug("found {} repositories", len(data["repositories"]))
                else:
                    log.warning(
                        "Docker registry {0} does not allow/support catalog search. (status={1})",
                        self.registry_url,
                        resp.status,
                    )
                    break
                catalog_url = None
                next_page_link = resp.links.get("next")
                if next_page_link:
                    next_page_url = cast(yarl.URL, next_page_link["url"])
                    catalog_url = self.registry_url.with_path(next_page_url.path).with_query(
                        next_page_url.query
                    )
