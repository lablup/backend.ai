from __future__ import annotations

import json
import logging
import urllib.parse
from typing import Any, AsyncIterator, Mapping, Optional, cast

import aiohttp
import aiohttp.client_exceptions
import aiotools
import yarl

from ai.backend.common.docker import ImageRef, arch_name_aliases
from ai.backend.common.docker import login as registry_login
from ai.backend.common.logging import BraceStyleAdapter

from .base import (
    BaseContainerRegistry,
    concurrency_sema,
    progress_reporter,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class HarborRegistry_v1(BaseContainerRegistry):
    async def fetch_repositories(
        self,
        sess: aiohttp.ClientSession,
    ) -> AsyncIterator[str]:
        api_url = self.registry_url / "api"
        registry_projects = self.registry_info["project"]
        rqst_args = {}
        if self.credentials:
            rqst_args["auth"] = aiohttp.BasicAuth(
                self.credentials["username"],
                self.credentials["password"],
            )
        project_list_url: Optional[yarl.URL]
        project_list_url = (api_url / "projects").with_query(
            {"page_size": "30"},
        )
        project_ids = []
        while project_list_url is not None:
            async with sess.get(project_list_url, allow_redirects=False, **rqst_args) as resp:
                projects = await resp.json()
                for item in projects:
                    if item["name"] in registry_projects:
                        project_ids.append(item["project_id"])
                project_list_url = None
                next_page_link = resp.links.get("next")
                if next_page_link:
                    next_page_url = cast(yarl.URL, next_page_link["url"])
                    project_list_url = self.registry_url.with_path(next_page_url.path).with_query(
                        next_page_url.query
                    )
        if not project_ids:
            log.warning("There is no given project.")
            return
        repo_list_url: Optional[yarl.URL]
        for project_id in project_ids:
            repo_list_url = (api_url / "repositories").with_query(
                {"project_id": project_id, "page_size": "30"},
            )
            while repo_list_url is not None:
                async with sess.get(repo_list_url, allow_redirects=False, **rqst_args) as resp:
                    items = await resp.json()
                    repos = [item["name"] for item in items]
                    for item in repos:
                        yield item
                    repo_list_url = None
                    next_page_link = resp.links.get("next")
                    if next_page_link:
                        next_page_url = cast(yarl.URL, next_page_link["url"])
                        repo_list_url = self.registry_url.with_path(next_page_url.path).with_query(
                            next_page_url.query
                        )

    async def _scan_tag(
        self,
        sess: aiohttp.ClientSession,
        rqst_args: dict[str, Any],
        image: str,
        tag: str,
    ) -> None:
        async with concurrency_sema.get():
            async with sess.get(
                self.registry_url / f"v2/{image}/manifests/{tag}", **rqst_args
            ) as resp:
                if resp.status == 404:
                    # ignore missing tags
                    # (may occur after deleting an image from the docker hub)
                    return
                resp.raise_for_status()
                data = await resp.json()

                config_digest = data["config"]["digest"]
                size_bytes = sum(layer["size"] for layer in data["layers"]) + data["config"]["size"]
                async with sess.get(
                    self.registry_url / f"v2/{image}/blobs/{config_digest}", **rqst_args
                ) as resp:
                    resp.raise_for_status()
                    data = json.loads(await resp.read())
                    architecture = arch_name_aliases.get(data["architecture"], data["architecture"])
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
                    manifest = {
                        architecture: {
                            "size": size_bytes,
                            "labels": labels,
                            "digest": config_digest,
                        },
                    }
        await self._read_manifest(image, tag, manifest)


class HarborRegistry_v2(BaseContainerRegistry):
    async def untag(
        self,
        image: ImageRef,
    ) -> None:
        project, repository = image.name.split("/", maxsplit=1)
        base_url = (
            self.registry_url
            / "api"
            / "v2.0"
            / "projects"
            / project
            / "repositories"
            / repository
            / "artifacts"
            / image.tag
        )
        username = self.registry_info["username"]
        if username is not None:
            self.credentials["username"] = username
        password = self.registry_info["password"]
        if password is not None:
            self.credentials["password"] = password

        async with self.prepare_client_session() as (url, sess):
            rqst_args = {}
            if self.credentials:
                rqst_args["auth"] = aiohttp.BasicAuth(
                    self.credentials["username"],
                    self.credentials["password"],
                )

            async with sess.delete(base_url, allow_redirects=False, **rqst_args) as resp:
                try:
                    resp.raise_for_status()
                except aiohttp.ClientResponseError as e:
                    if (
                        e.status != 404
                    ):  #  404 means image is already removed from harbor so we can just safely ignore the exception
                        raise RuntimeError(f"Failed to untag {image}: {e.message}") from e

    async def fetch_repositories(
        self,
        sess: aiohttp.ClientSession,
    ) -> AsyncIterator[str]:
        api_url = self.registry_url / "api" / "v2.0"
        registry_projects = self.registry_info["project"]
        rqst_args = {}
        if self.credentials:
            rqst_args["auth"] = aiohttp.BasicAuth(
                self.credentials["username"],
                self.credentials["password"],
            )
        repo_list_url: Optional[yarl.URL]
        for project_name in registry_projects:
            repo_list_url = (api_url / "projects" / project_name / "repositories").with_query(
                {"page_size": "30"},
            )
            while repo_list_url is not None:
                async with sess.get(repo_list_url, allow_redirects=False, **rqst_args) as resp:
                    items = await resp.json()
                    if isinstance(items, dict) and (errors := items.get("errors", [])):
                        raise RuntimeError(
                            f"failed to fetch repositories in project {project_name}",
                            errors[0]["code"],
                            errors[0]["message"],
                        )
                    repos = [item["name"] for item in items]
                    for item in repos:
                        yield item
                    repo_list_url = None
                    next_page_link = resp.links.get("next")
                    if next_page_link:
                        next_page_url = cast(yarl.URL, next_page_link["url"])
                        repo_list_url = self.registry_url.with_path(next_page_url.path).with_query(
                            next_page_url.query
                        )

    async def _scan_image(
        self,
        sess: aiohttp.ClientSession,
        image: str,
    ) -> None:
        api_url = self.registry_url / "api" / "v2.0"
        rqst_args = await registry_login(
            sess,
            self.registry_url,
            self.credentials,
            f"repository:{image}:pull",
        )
        if self.credentials:
            rqst_args["auth"] = aiohttp.BasicAuth(
                self.credentials["username"],
                self.credentials["password"],
            )
        project, _, repository = image.partition("/")
        project, repository = [urllib.parse.urlencode({"": x})[1:] for x in [project, repository]]
        async with aiotools.TaskGroup() as tg:
            artifact_url: Optional[yarl.URL] = (
                api_url / "projects" / project / "repositories" / repository / "artifacts"
            ).with_query(
                {"page_size": "30"},
            )
            while artifact_url is not None:
                async with sess.get(artifact_url, allow_redirects=False, **rqst_args) as resp:
                    resp.raise_for_status()
                    body = await resp.json()
                    for image_info in body:
                        skip_reason: Optional[str] = None
                        tag = image_info["digest"]
                        try:
                            if not image_info["tags"] or len(image_info["tags"]) == 0:
                                skip_reason = "no tag"
                                continue
                            tag = image_info["tags"][0]["name"]
                            match image_info["manifest_media_type"]:
                                case self.MEDIA_TYPE_OCI_INDEX:
                                    await self._process_oci_index(
                                        tg, sess, rqst_args, image, image_info
                                    )
                                case self.MEDIA_TYPE_DOCKER_MANIFEST_LIST:
                                    await self._process_docker_v2_multiplatform_image(
                                        tg, sess, rqst_args, image, image_info
                                    )
                                case self.MEDIA_TYPE_DOCKER_MANIFEST:
                                    await self._process_docker_v2_image(
                                        tg, sess, rqst_args, image, image_info
                                    )
                                case _ as media_type:
                                    raise RuntimeError(
                                        f"Unsupported artifact media-type: {media_type}"
                                    )
                        finally:
                            if skip_reason:
                                log.warning("Skipped image - {}:{} ({})", image, tag, skip_reason)
                    artifact_url = None
                    next_page_link = resp.links.get("next")
                    if next_page_link:
                        next_page_url = cast(yarl.URL, next_page_link["url"])
                        artifact_url = self.registry_url.with_path(next_page_url.path).with_query(
                            next_page_url.query
                        )

    async def _scan_tag(
        self,
        sess: aiohttp.ClientSession,
        rqst_args: dict[str, Any],
        image: str,
        tag: str,
    ) -> None:
        project, _, repository = image.partition("/")
        project, repository, tag = [
            urllib.parse.urlencode({"": x})[1:] for x in [project, repository, tag]
        ]
        api_url = self.registry_url / "api" / "v2.0"
        rqst_args["headers"] = {}
        async with sess.get(
            api_url / "projects" / project / "repositories" / repository / "artifacts" / tag,
            **rqst_args,
        ) as resp:
            if resp.status == 404:
                # ignore missing tags
                # (may occur after deleting an image from the docker hub)
                return
            resp.raise_for_status()
            resp_json = await resp.json()
            async with aiotools.TaskGroup() as tg:
                match resp_json["manifest_media_type"]:
                    case self.MEDIA_TYPE_OCI_INDEX:
                        await self._process_oci_index(tg, sess, rqst_args, image, resp_json)
                    case self.MEDIA_TYPE_DOCKER_MANIFEST_LIST:
                        await self._process_docker_v2_multiplatform_image(
                            tg, sess, rqst_args, image, resp_json
                        )
                    case self.MEDIA_TYPE_DOCKER_MANIFEST:
                        await self._process_docker_v2_image(tg, sess, rqst_args, image, resp_json)
                    case _ as media_type:
                        raise RuntimeError(f"Unsupported artifact media-type: {media_type}")

    async def _process_oci_index(
        self,
        tg: aiotools.TaskGroup,
        sess: aiohttp.ClientSession,
        _rqst_args: Mapping[str, Any],
        image: str,
        image_info: Mapping[str, Any],
    ) -> None:
        rqst_args = dict(_rqst_args)
        if not rqst_args.get("headers"):
            rqst_args["headers"] = {}
        rqst_args["headers"].update({"Accept": "application/vnd.oci.image.manifest.v1+json"})
        digests: list[tuple[str, str]] = []
        tag_name = image_info["tags"][0]["name"]
        for reference in image_info["references"]:
            if (
                reference["platform"]["os"] == "unknown"
                or reference["platform"]["architecture"] == "unknown"
            ):
                continue
            digests.append((reference["child_digest"], reference["platform"]["architecture"]))
        if (reporter := progress_reporter.get()) is not None:
            reporter.total_progress += len(digests)
        async with aiotools.TaskGroup() as tg:
            for digest, architecture in digests:
                tg.create_task(
                    self._harbor_scan_tag_per_arch(
                        sess,
                        rqst_args,
                        image,
                        digest=digest,
                        tag=tag_name,
                        architecture=architecture,
                    )
                )

    async def _process_docker_v2_multiplatform_image(
        self,
        tg: aiotools.TaskGroup,
        sess: aiohttp.ClientSession,
        _rqst_args: Mapping[str, Any],
        image: str,
        image_info: Mapping[str, Any],
    ) -> None:
        rqst_args = dict(_rqst_args)
        if not rqst_args.get("headers"):
            rqst_args["headers"] = {}
        rqst_args["headers"].update({
            "Accept": "application/vnd.docker.distribution.manifest.v2+json"
        })
        digests: list[tuple[str, str]] = []
        tag_name = image_info["tags"][0]["name"]
        for reference in image_info["references"]:
            if (
                reference["platform"]["os"] == "unknown"
                or reference["platform"]["architecture"] == "unknown"
            ):
                continue
            digests.append((reference["child_digest"], reference["platform"]["architecture"]))
        if (reporter := progress_reporter.get()) is not None:
            reporter.total_progress += len(digests)
        async with aiotools.TaskGroup() as tg:
            for digest, architecture in digests:
                tg.create_task(
                    self._harbor_scan_tag_per_arch(
                        sess,
                        rqst_args,
                        image,
                        digest=digest,
                        tag=tag_name,
                        architecture=architecture,
                    )
                )

    async def _process_docker_v2_image(
        self,
        tg: aiotools.TaskGroup,
        sess: aiohttp.ClientSession,
        _rqst_args: Mapping[str, Any],
        image: str,
        image_info: Mapping[str, Any],
    ) -> None:
        rqst_args = dict(_rqst_args)
        if not rqst_args.get("headers"):
            rqst_args["headers"] = {}
        rqst_args["headers"].update({
            "Accept": "application/vnd.docker.distribution.manifest.v2+json"
        })
        if (reporter := progress_reporter.get()) is not None:
            reporter.total_progress += 1
        tag_name = image_info["tags"][0]["name"]
        async with aiotools.TaskGroup() as tg:
            tg.create_task(
                self._harbor_scan_tag_single_arch(
                    sess,
                    rqst_args,
                    image,
                    tag=tag_name,
                )
            )

    async def _harbor_scan_tag_per_arch(
        self,
        sess: aiohttp.ClientSession,
        rqst_args: dict[str, Any],
        image: str,
        *,
        digest: str,
        tag: str,
        architecture: str,
    ) -> None:
        """
        Scan 'image:tag' when there are explicitly known values of digest and architecture.
        """
        manifests = {}
        async with concurrency_sema.get():
            async with sess.get(
                self.registry_url / f"v2/{image}/manifests/{digest}", **rqst_args
            ) as resp:
                if resp.status == 404:
                    # ignore missing tags
                    # (may occur after deleting an image from the docker hub)
                    return
                resp.raise_for_status()
                top_manifest = await resp.json()
            architecture = arch_name_aliases.get(architecture, architecture)
            config_digest = top_manifest["config"]["digest"]
            size_bytes = (
                sum(layer["size"] for layer in top_manifest["layers"])
                + top_manifest["config"]["size"]
            )
            async with sess.get(
                self.registry_url / f"v2/{image}/blobs/{config_digest}", **rqst_args
            ) as resp:
                resp.raise_for_status()
                data = json.loads(await resp.read())
            labels = {}
            if _config_labels := data.get("config", {}).get("Labels"):
                labels = _config_labels
            elif _container_config_labels := data.get("container_config", {}).get("Labels"):
                labels = _container_config_labels

            if not labels:
                log.warning("Labels section not found on image {}:{}/{}", image, tag, architecture)

            manifests[architecture] = {
                "size": size_bytes,
                "labels": labels,
                "digest": config_digest,
            }
            await self._read_manifest(image, tag, manifests)

    async def _harbor_scan_tag_single_arch(
        self,
        sess: aiohttp.ClientSession,
        rqst_args: dict[str, Any],
        image: str,
        tag: str,
    ) -> None:
        """
        Scan 'image:tag' which has been pusehd as a single architecture tag.
        In this case, Harbor does not provide explicit methods to determine the architecture.
        We infer the architecture from the tag naming patterns ("-arm64" for instance).
        """
        manifests = {}
        async with concurrency_sema.get():
            rqst_args["headers"]["Accept"] = self.MEDIA_TYPE_DOCKER_MANIFEST
            # Harbor does not provide architecture information for a single-arch tag reference.
            # We heuristically detect the architecture using the tag name pattern.
            if tag.endswith("-arm64") or tag.endswith("-aarch64"):
                architecture = "aarch64"
            else:
                architecture = "x86_64"
            async with sess.get(
                self.registry_url / f"v2/{image}/manifests/{tag}", **rqst_args
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
            if _config_labels := data.get("config", {}).get("Labels"):
                labels = _config_labels
            elif _container_config_labels := data.get("container_config", {}).get("Labels"):
                labels = _container_config_labels

            if not labels:
                log.warning("Labels section not found on image {}:{}/{}", image, tag, architecture)
            manifests[architecture] = {
                "size": size_bytes,
                "labels": labels,
                "digest": config_digest,
            }
            await self._read_manifest(image, tag, manifests)
