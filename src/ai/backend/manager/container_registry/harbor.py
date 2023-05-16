import logging
import urllib.parse
from typing import Any, AsyncIterator, Mapping, Optional, cast

import aiohttp
import aiotools
import yarl

from ai.backend.common.docker import login as registry_login
from ai.backend.common.logging import BraceStyleAdapter

from .base import BaseContainerRegistry

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


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


class HarborRegistry_v2(BaseContainerRegistry):
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
                                return
                            tag = image_info["tags"][0]["name"]
                            match image_info["manifest_media_type"]:
                                case "application/vnd.oci.image.index.v1+json":
                                    await self._process_oci_index(
                                        tg, sess, rqst_args, image, image_info
                                    )
                                case "application/vnd.docker.distribution.manifest.list.v2+json":
                                    await self._process_docker_v2_multiplatform_image(
                                        tg, sess, rqst_args, image, image_info
                                    )
                                case _:
                                    await self._process_docker_v2_image(
                                        tg, sess, rqst_args, image, image_info
                                    )
                        finally:
                            if skip_reason:
                                log.warn("Skipped image - {}:{} ({})", image, tag, skip_reason)
                    artifact_url = None
                    next_page_link = resp.links.get("next")
                    if next_page_link:
                        next_page_url = cast(yarl.URL, next_page_link["url"])
                        artifact_url = self.registry_url.with_path(next_page_url.path).with_query(
                            next_page_url.query
                        )

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
        digests: list[str] = []
        for reference in image_info["references"]:
            if (
                reference["platform"]["os"] == "unknown"
                or reference["platform"]["architecture"] == "unknown"
            ):
                continue
            digests.append(reference["child_digest"])
        if (reporter := self.reporter.get()) is not None:
            reporter.total_progress += len(digests)
        async with aiotools.TaskGroup() as tg:
            for digest in digests:
                tg.create_task(
                    self._scan_tag(
                        sess, rqst_args, image, digest, tag=image_info["tags"][0]["name"]
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
        rqst_args["headers"].update(
            {"Accept": "application/vnd.docker.distribution.manifest.v2+json"}
        )
        digests: list[str] = []
        for reference in image_info["references"]:
            if (
                reference["platform"]["os"] == "unknown"
                or reference["platform"]["architecture"] == "unknown"
            ):
                continue
            digests.append(reference["child_digest"])
        if (reporter := self.reporter.get()) is not None:
            reporter.total_progress += len(digests)
        async with aiotools.TaskGroup() as tg:
            for digest in digests:
                tg.create_task(
                    self._scan_tag(
                        sess, rqst_args, image, digest, tag=image_info["tags"][0]["name"]
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
        rqst_args["headers"].update(
            {"Accept": "application/vnd.docker.distribution.manifest.v2+json"}
        )
        if (reporter := self.reporter.get()) is not None:
            reporter.total_progress += 1
        async with aiotools.TaskGroup() as tg:
            tg.create_task(self._scan_tag(sess, rqst_args, image, image_info["tags"][0]["name"]))
