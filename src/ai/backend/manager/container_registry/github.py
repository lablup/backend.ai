import asyncio
import json
import logging
from typing import AsyncIterator, Optional, cast

import aiohttp
import aiotools
import yarl

from ai.backend.common.bgtask import ProgressReporter
from ai.backend.common.logging import BraceStyleAdapter

from .base import (
    BaseContainerRegistry,
    all_updates,
    concurrency_sema,
    progress_reporter,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class GitHubRegistry_v2(BaseContainerRegistry):
    async def fetch_repositories(
        self,
        sess: aiohttp.ClientSession,
    ) -> AsyncIterator[str]:
        name, type_, access_token = (
            self.registry_info["name"],
            self.registry_info["name_type"],
            self.registry_info["token"],
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
                        yield repo["name"]
                    if "next" in response.links:
                        page += 1
                    else:
                        break
                else:
                    print(f"Failed to fetch repositories: {response.status}")
                    break

    async def get_ghcr_token(self, image: str):
        url = f"https://ghcr.io/token?scope=repository:{image}:pull"
        auth = aiohttp.BasicAuth(
            login=self.registry_info["name"], password=self.registry_info["token"]
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(url, auth=auth) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["token"]
                else:
                    raise Exception("Failed to get token")

    async def rescan_single_registry(
        self,
        reporter: ProgressReporter | None = None,
    ) -> None:
        log.info("rescan_single_registry()")
        all_updates_token = all_updates.set({})
        concurrency_sema.set(asyncio.Semaphore(self.max_concurrency_per_registry))
        progress_reporter.set(reporter)
        try:
            username = self.registry_info["name"]
            if username is not None:
                self.credentials["username"] = username
            password = self.registry_info["token"]
            if password is not None:
                self.credentials["password"] = password
            async with self.prepare_client_session() as (url, client_session):
                self.registry_url = url
                async with aiotools.TaskGroup() as tg:
                    async for image in self.fetch_repositories(client_session):
                        tg.create_task(
                            self._scan_image(
                                client_session, f"{self.registry_info["name"]}/{image}"
                            )
                        )
            await self.commit_rescan_result()
        finally:
            all_updates.reset(all_updates_token)

    async def _scan_image(
        self,
        sess: aiohttp.ClientSession,
        image: str,
    ) -> None:
        log.info("_scan_image()")

        ghcr_token = await self.get_ghcr_token(
            image,
        )

        tags = []
        tag_list_url: Optional[yarl.URL]
        tag_list_url = (self.registry_url / f"v2/{image}/tags/list").with_query(
            {"n": "10"},
        )
        rqst_args = {"headers": {"Authorization": f"Bearer {ghcr_token}"}}

        while tag_list_url is not None:
            async with sess.get(tag_list_url, allow_redirects=False, **rqst_args) as resp:
                data = json.loads(await resp.read())

                if "tags" in data:
                    # sometimes there are dangling image names in the hub.
                    tags.extend(data["tags"])
                tag_list_url = None
                next_page_link = resp.links.get("next")
                if next_page_link:
                    next_page_url = cast(yarl.URL, next_page_link["url"])
                    tag_list_url = self.registry_url.with_path(next_page_url.path).with_query(
                        next_page_url.query
                    )

        if (reporter := progress_reporter.get()) is not None:
            reporter.total_progress += len(tags)

        async with aiotools.TaskGroup() as tg:
            for tag in tags:
                tg.create_task(self._scan_tag(sess, rqst_args, image, tag))

    # async def _scan_tag(self, sess: aiohttp.ClientSession, image: str):
    #     url = f"https://ghcr.io/v2/{image}/tags/list"
    #     headers = {'Authorization': f'Bearer {token}'}
    #     async with aiohttp.ClientSession() as session:
    #         async with session.get(url, headers=headers) as response:
    #             if response.status == 200:
    #                 data = await response.json()
    #                 return data
    #             else:
    #                 print('response.status', response.status)
    #                 print("Failed to fetch tags")
    #                 return {}

    # async def _scan_image(self):
    #     pass

    # async def _read_manifest(self):
    #     pass
