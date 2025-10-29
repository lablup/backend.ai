import logging
from http import HTTPStatus
from typing import AsyncIterator, Optional, cast, override

import aiohttp
import yarl

from ai.backend.common.docker import login as registry_login
from ai.backend.common.json import read_json
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.exceptions import ContainerRegistryProjectEmpty

from .base import BaseContainerRegistry

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class OpenShiftPlatformContainerRegistry(BaseContainerRegistry):
    @override
    async def fetch_repositories(
        self,
        sess: aiohttp.ClientSession,
    ) -> AsyncIterator[str]:
        if not self.registry_info.project:
            raise ContainerRegistryProjectEmpty(self.registry_info.type, self.registry_info.project)

        # OpenShift Container Registry uses Docker Registry API v2
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
                if resp.status == HTTPStatus.OK:
                    data = await read_json(resp)

                    for item in data["repositories"]:
                        if item.startswith(self.registry_info.project):
                            yield item
                    log.debug("found {} repositories", len(data["repositories"]))
                else:
                    log.warning(
                        "OpenShift Container Registry {0} does not allow/support catalog search. (status={1})",
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
