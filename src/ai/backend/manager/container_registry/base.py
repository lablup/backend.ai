from __future__ import annotations

import asyncio
import json
import logging
from abc import ABCMeta, abstractmethod
from contextlib import asynccontextmanager as actxmgr
from contextvars import ContextVar
from typing import Any, AsyncIterator, Dict, Final, Mapping, Optional, cast

import aiohttp
import aiotools
import sqlalchemy as sa
import trafaret as t
import yarl

from ai.backend.common.bgtask import ProgressReporter
from ai.backend.common.docker import ImageRef, arch_name_aliases, validate_image_labels
from ai.backend.common.docker import login as registry_login
from ai.backend.common.exception import InvalidImageName, InvalidImageTag
from ai.backend.common.logging import BraceStyleAdapter

from ...common.types import SSLContextType
from ..models.image import ImageRow, ImageType
from ..models.utils import ExtendedAsyncSAEngine

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]
concurrency_sema: ContextVar[asyncio.Semaphore] = ContextVar("concurrency_sema")
progress_reporter: ContextVar[Optional[ProgressReporter]] = ContextVar(
    "progress_reporter", default=None
)
all_updates: ContextVar[Dict[ImageRef, Dict[str, Any]]] = ContextVar("all_updates")


class BaseContainerRegistry(metaclass=ABCMeta):
    db: ExtendedAsyncSAEngine
    registry_name: str
    registry_info: Mapping[str, Any]
    registry_url: yarl.URL
    max_concurrency_per_registry: int
    base_hdrs: Dict[str, str]
    credentials: Dict[str, str]
    ssl_verify: bool

    MEDIA_TYPE_OCI_INDEX: Final[str] = "application/vnd.oci.image.index.v1+json"
    MEDIA_TYPE_OCI_MANIFEST: Final[str] = "application/vnd.oci.image.manifest.v1+json"
    MEDIA_TYPE_DOCKER_MANIFEST_LIST: Final[str] = (
        "application/vnd.docker.distribution.manifest.list.v2+json"
    )
    MEDIA_TYPE_DOCKER_MANIFEST: Final[str] = "application/vnd.docker.distribution.manifest.v2+json"

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        registry_name: str,
        registry_info: Mapping[str, Any],
        *,
        max_concurrency_per_registry: int = 4,
        ssl_verify: bool = True,
    ) -> None:
        self.db = db
        self.registry_name = registry_name
        self.registry_info = registry_info
        self.registry_url = registry_info[""]
        self.max_concurrency_per_registry = max_concurrency_per_registry
        self.base_hdrs = {
            "Accept": "application/vnd.docker.distribution.manifest.v2+json",
        }
        self.credentials = {}
        self.ssl_verify = ssl_verify

    @actxmgr
    async def prepare_client_session(self) -> AsyncIterator[tuple[yarl.URL, aiohttp.ClientSession]]:
        ssl_ctx: SSLContextType = True  # default
        if not self.registry_info["ssl_verify"]:
            ssl_ctx = False
        connector = aiohttp.TCPConnector(ssl=ssl_ctx)
        async with aiohttp.ClientSession(connector=connector) as sess:
            yield self.registry_url, sess

    async def rescan_single_registry(
        self,
        reporter: ProgressReporter | None = None,
    ) -> None:
        log.info("rescan_single_registry()")
        all_updates_token = all_updates.set({})
        concurrency_sema.set(asyncio.Semaphore(self.max_concurrency_per_registry))
        progress_reporter.set(reporter)
        try:
            username = self.registry_info["username"]
            if username is not None:
                self.credentials["username"] = username
            password = self.registry_info["password"]
            if password is not None:
                self.credentials["password"] = password
            async with self.prepare_client_session() as (url, client_session):
                self.registry_url = url
                async with aiotools.TaskGroup() as tg:
                    async for image in self.fetch_repositories(client_session):
                        tg.create_task(self._scan_image(client_session, image))
            await self.commit_rescan_result()
        finally:
            all_updates.reset(all_updates_token)

    async def commit_rescan_result(self) -> None:
        _all_updates = all_updates.get()
        if not _all_updates:
            log.info("No images found in registry {0}", self.registry_url)
        else:
            image_identifiers = [(k.canonical, k.architecture) for k in _all_updates.keys()]
            async with self.db.begin_session() as session:
                existing_images = await session.scalars(
                    sa.select(ImageRow).where(
                        sa.func.ROW(ImageRow.name, ImageRow.architecture).in_(image_identifiers),
                    ),
                )
                is_local = self.registry_name == "local"

                for image_row in existing_images:
                    key = image_row.image_ref
                    values = _all_updates.get(key)
                    if values is None:
                        continue
                    _all_updates.pop(key)
                    image_row.config_digest = values["config_digest"]
                    image_row.size_bytes = values["size_bytes"]
                    image_row.accelerators = values.get("accels")
                    image_row.labels = values["labels"]
                    image_row.is_local = is_local
                    image_row.resources = values["resources"]

                session.add_all([
                    ImageRow(
                        name=k.canonical,
                        registry=k.registry,
                        image=k.name,
                        tag=k.tag,
                        architecture=k.architecture,
                        is_local=is_local,
                        config_digest=v["config_digest"],
                        size_bytes=v["size_bytes"],
                        type=ImageType.COMPUTE,
                        accelerators=v.get("accels"),
                        labels=v["labels"],
                        resources=v["resources"],
                    )
                    for k, v in _all_updates.items()
                ])
                await session.flush()

    async def scan_single_ref(self, image_ref: str) -> None:
        all_updates_token = all_updates.set({})
        sema_token = concurrency_sema.set(asyncio.Semaphore(1))
        try:
            username = self.registry_info["username"]
            if username is not None:
                self.credentials["username"] = username
            password = self.registry_info["password"]
            if password is not None:
                self.credentials["password"] = password
            async with self.prepare_client_session() as (url, sess):
                image, tag = ImageRef._parse_image_tag(image_ref)
                rqst_args = await registry_login(
                    sess,
                    self.registry_url,
                    self.credentials,
                    f"repository:{image}:pull",
                )
                rqst_args["headers"].update(**self.base_hdrs)
                await self._scan_tag(sess, rqst_args, image, tag)
            await self.commit_rescan_result()
        finally:
            concurrency_sema.reset(sema_token)
            all_updates.reset(all_updates_token)

    async def _scan_image(
        self,
        sess: aiohttp.ClientSession,
        image: str,
    ) -> None:
        log.info("_scan_image()")
        rqst_args = await registry_login(
            sess,
            self.registry_url,
            self.credentials,
            f"repository:{image}:pull",
        )
        rqst_args["headers"].update(**self.base_hdrs)
        tags = []
        tag_list_url: Optional[yarl.URL]
        tag_list_url = (self.registry_url / f"v2/{image}/tags/list").with_query(
            {"n": "10"},
        )
        while tag_list_url is not None:
            async with sess.get(tag_list_url, **rqst_args) as resp:
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

    async def _scan_tag(
        self,
        sess: aiohttp.ClientSession,
        rqst_args: dict[str, Any],
        image: str,
        tag: str,
    ) -> None:
        manifests = {}
        async with concurrency_sema.get():
            rqst_args["headers"]["Accept"] = self.MEDIA_TYPE_DOCKER_MANIFEST_LIST
            async with sess.get(
                self.registry_url / f"v2/{image}/manifests/{tag}", **rqst_args
            ) as resp:
                if resp.status == 404:
                    # ignore missing tags
                    # (may occur after deleting an image from the docker hub)
                    return
                content_type = resp.headers["Content-Type"]
                resp.raise_for_status()
                resp_json = await resp.json()
                match content_type:
                    case self.MEDIA_TYPE_DOCKER_MANIFEST_LIST:
                        manifest_list = resp_json["manifests"]
                        request_type = self.MEDIA_TYPE_DOCKER_MANIFEST
                    case self.MEDIA_TYPE_OCI_INDEX:
                        manifest_list = [
                            item
                            for item in resp_json["manifests"]
                            if "annotations" not in item  # skip attestation manifests
                        ]
                        request_type = self.MEDIA_TYPE_OCI_MANIFEST
                    case _:
                        log.warn("Unknown content type: {}", content_type)
                        raise RuntimeError(
                            "The registry does not support the standard way of "
                            "listing multiarch images."
                        )
            rqst_args["headers"]["Accept"] = request_type
            for manifest in manifest_list:
                platform_arg = (
                    f"{manifest['platform']['os']}/{manifest['platform']['architecture']}"
                )
                if variant := manifest["platform"].get("variant", None):
                    platform_arg += f"/{variant}"
                architecture = manifest["platform"]["architecture"]
                architecture = arch_name_aliases.get(architecture, architecture)
                async with sess.get(
                    self.registry_url / f"v2/{image}/manifests/{manifest['digest']}", **rqst_args
                ) as resp:
                    data = await resp.json()
                config_digest = data["config"]["digest"]
                size_bytes = sum(layer["size"] for layer in data["layers"]) + data["config"]["size"]
                async with sess.get(
                    self.registry_url / f"v2/{image}/blobs/{config_digest}", **rqst_args
                ) as resp:
                    resp.raise_for_status()
                    data = json.loads(await resp.read())
                labels = {}
                # we should favor `config` instead of `container_config` since `config` can contain additional datas
                # set when commiting image via `--change` flag
                if _config_labels := data.get("config", {}).get("Labels"):
                    labels = _config_labels
                elif _container_config_labels := data.get("container_config", {}).get("Labels"):
                    labels = _container_config_labels

                if not labels:
                    log.warning(
                        "Labels section not found on image {}:{}/{}", image, tag, architecture
                    )

                manifests[architecture] = {
                    "size": size_bytes,
                    "labels": labels,
                    "digest": config_digest,
                }
            await self._read_manifest(image, tag, manifests)

    async def _read_manifest(
        self,
        image: str,
        tag: str,
        manifests: dict[str, dict],
        skip_reason: Optional[str] = None,
    ) -> None:
        if not manifests:
            if not skip_reason:
                skip_reason = "missing/deleted"
            log.warning("Skipped image - {}:{} ({})", image, tag, skip_reason)
            progress_msg = f"Skipped {image}:{tag} ({skip_reason})"
            if (reporter := progress_reporter.get()) is not None:
                await reporter.update(1, message=progress_msg)
            return

        assert ImageRow.resources is not None
        for architecture, manifest in manifests.items():
            try:
                try:
                    validate_image_labels(manifest["labels"])
                except t.DataError as e:
                    match e.as_dict():
                        case str() as error_msg:
                            skip_reason = error_msg
                        case dict() as error_data:
                            skip_reason = "; ".join(
                                f"{field} {reason}" for field, reason in error_data.items()
                            )
                    continue
                except ValueError as e:
                    skip_reason = str(e)
                    continue
                if self.registry_name == "local":
                    if image.partition("/")[1] == "":
                        image = "library/" + image
                    update_key = ImageRef(
                        f"{image}:{tag}",
                        ["index.docker.io"],
                        architecture,
                    )
                else:
                    update_key = ImageRef(
                        f"{self.registry_name}/{image}:{tag}",
                        [self.registry_name],
                        architecture,
                    )
                updates = {
                    "config_digest": manifest["digest"],
                    "size_bytes": manifest["size"],
                    "labels": manifest["labels"],  # keep the original form
                }
                accels = manifest["labels"].get("ai.backend.accelerators")
                if accels:
                    updates["accels"] = accels

                resources = {  # default fallback if not defined
                    "cpu": {"min": "1", "max": None},
                    "mem": {"min": "1g", "max": None},
                }
                res_prefix = "ai.backend.resource.min."
                for k, v in filter(
                    lambda pair: pair[0].startswith(res_prefix), manifest["labels"].items()
                ):
                    res_key = k[len(res_prefix) :]
                    resources[res_key] = {"min": v}
                updates["resources"] = ImageRow.resources.type._schema.check(resources)
                all_updates.get().update({
                    update_key: updates,
                })
            except (InvalidImageName, InvalidImageTag) as e:
                skip_reason = str(e)
            finally:
                if skip_reason:
                    log.warning(
                        "Skipped image - {}:{}/{} ({})", image, tag, architecture, skip_reason
                    )
                    progress_msg = f"Skipped {image}:{tag}/{architecture} ({skip_reason})"
                else:
                    log.info(
                        "Updated image - {0}:{1}/{2} ({3})",
                        image,
                        tag,
                        architecture,
                        manifest["digest"],
                    )
                    progress_msg = f"Updated {image}:{tag}/{architecture} ({manifest['digest']})"
                if (reporter := progress_reporter.get()) is not None:
                    await reporter.update(1, message=progress_msg)

    @abstractmethod
    async def fetch_repositories(
        self,
        sess: aiohttp.ClientSession,
    ) -> AsyncIterator[str]:
        yield ""
