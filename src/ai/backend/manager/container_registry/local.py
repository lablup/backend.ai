import json
import logging
from typing import AsyncIterator

import aiohttp
import yarl

from ai.backend.common.docker import get_docker_connector
from ai.backend.common.logging import BraceStyleAdapter

from .base import BaseContainerRegistry

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class LocalRegistry(BaseContainerRegistry):
    async def prepare_client_session(self) -> AsyncIterator[tuple[yarl.URL, aiohttp.ClientSession]]:
        url, connector = get_docker_connector()
        async with aiohttp.ClientSession(connector=connector) as sess:
            yield url, sess

    async def fetch_repositories(
        self,
        sess: aiohttp.ClientSession,
    ) -> AsyncIterator[str]:
        async with sess.get(self.registry_url / "images" / "json") as response:
            items = await response.json()
            if (reporter := self.reporter.get()) is not None:
                reporter.total_progress = len(items)
            for item in items:
                labels = item["Labels"]
                if not labels:
                    continue
                if "ai.backend.kernelspec" in labels:
                    for image_ref_str in item["RepoTags"]:
                        if image_ref_str == "<none>:<none>":
                            # cache images
                            continue
                        yield image_ref_str  # this includes the tag part

    async def _scan_image(
        self,
        sess: aiohttp.ClientSession,
        image: str,
    ) -> None:
        repo, _, tag = image.rpartition(":")
        await self._scan_tag(sess, {}, repo, tag)

    async def _scan_tag(
        self,
        sess: aiohttp.ClientSession,
        rqst_args: dict[str, str],
        image: str,
        tag: str,
    ) -> None:
        async def _read_image_info(_tag: str):
            async with sess.get(
                self.registry_url / "images" / f"{image}:{tag}" / "json"
            ) as response:
                data = await response.json()
                architecture = data["Architecture"]
                if (reporter := self.reporter.get()) is not None:
                    reporter.total_progress += 1
                summary = {
                    "Id": data["Id"],
                    "RepoDigests": data["RepoDigests"],
                    "Config.Image": data["Config"]["Image"],
                    "ContainerConfig.Image": data["ContainerConfig"]["Image"],
                    "Architecture": data["Architecture"],
                }
                log.debug(
                    "Scanned image info: {}:{}\n{}", image, tag, json.dumps(summary, indent=2)
                )
                if not data["RepoDigests"]:
                    # images not pushed to registry v2 do not have the manifest yet.
                    digest = data["Id"]
                else:
                    digest = data["RepoDigests"][0].rpartition("@")[2]
                return {
                    architecture: {
                        "size": data["Size"],
                        "labels": data["Config"]["Labels"],
                        "digest": digest,
                    },
                }

        async with self.sema.get():
            manifests = await _read_image_info(tag)
        if manifests:
            await self._read_manifest(image, tag, manifests)
