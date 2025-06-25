"""
Written by claude
"""

import logging
from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import quote

import aiohttp

_PAGE_SIZE = 30


@dataclass
class HarborRegistryRawScannerArgs:
    registry_url: str
    username: Optional[str] = None
    password: Optional[str] = None


class HarborRegistryRawScanner:
    """
    Harbor scanner intended for testing the image scanner of Backend.AI.
    Do not use it for purposes other than testing.
    """

    def __init__(self, args: HarborRegistryRawScannerArgs):
        self._registry_url = args.registry_url.rstrip("/")
        self._username = args.username
        self._password = args.password
        self._session: Optional[aiohttp.ClientSession] = None

        logging.basicConfig(level=logging.INFO)
        self._logger = logging.getLogger(__name__)

    async def __aenter__(self):
        connector = aiohttp.TCPConnector(ssl=False)
        timeout = aiohttp.ClientTimeout(total=30)

        # Only use authentication if both username and password are provided
        auth = None
        if self._username and self._password:
            auth = aiohttp.BasicAuth(self._username, self._password)

        self._session = aiohttp.ClientSession(auth=auth, connector=connector, timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()

    async def _make_request(
        self, endpoint: str, params: Optional[dict] = None
    ) -> list[dict[str, Any]]:
        if not self._session:
            raise RuntimeError("Session not initialized")

        url = f"{self._registry_url}{endpoint}"
        all_results = []
        page = 1

        while True:
            request_params = {"page": page, "page_size": _PAGE_SIZE}
            if params:
                request_params.update(params)

            try:
                async with self._session.get(url, params=request_params) as response:
                    if response.status == 404:
                        break
                    elif response.status in (401, 403):
                        self._logger.error(
                            f"Authentication required for {url}. Status: {response.status}"
                        )
                        break
                    response.raise_for_status()

                    data = await response.json()
                    if not data:
                        break

                    all_results.extend(data)

                    if len(data) < _PAGE_SIZE:
                        break

                    page += 1

            except aiohttp.ClientError as e:
                self._logger.error(f"Request failed for {url}: {e}")
                break

        return all_results

    async def get_projects(self) -> list[dict[str, Any]]:
        projects = await self._make_request("/api/v2.0/projects")
        return projects

    async def get_repositories(self, project_name: str) -> list[dict[str, Any]]:
        encoded_project = quote(project_name, safe="")
        endpoint = f"/api/v2.0/projects/{encoded_project}/repositories"
        repositories = await self._make_request(endpoint)
        return repositories

    async def get_artifacts(self, project_name: str, repository_name: str) -> list[dict[str, Any]]:
        encoded_project = quote(project_name, safe="")
        encoded_repo = quote(repository_name, safe="")
        endpoint = f"/api/v2.0/projects/{encoded_project}/repositories/{encoded_repo}/artifacts"

        params = {"with_tag": "true", "with_scan_overview": "false"}
        artifacts = await self._make_request(endpoint, params)
        return artifacts

    def generate_canonical_names(
        self,
        harbor_host: str,
        project_name: str,
        repository_name: str,
        artifacts: list[dict[str, Any]],
    ) -> list[str]:
        canonical_names = []

        for artifact in artifacts:
            tags = artifact.get("tags", [])

            # Skip artifacts without tags
            if tags:
                for tag in tags:
                    tag_name = tag.get("name", "")
                    if tag_name:
                        canonical_name = (
                            f"{harbor_host}/{project_name}/{repository_name}:{tag_name}"
                        )
                        canonical_names.append(canonical_name)

        return canonical_names

    async def scan_all_images(self) -> list[str]:
        harbor_host = self._registry_url.replace("http://", "").replace("https://", "")
        all_canonical_names = []

        try:
            projects = await self.get_projects()

            for project in projects:
                project_name = project.get("name", "")
                if not project_name:
                    continue

                try:
                    repositories = await self.get_repositories(project_name)

                    for repository in repositories:
                        repo_name = repository.get("name", "")
                        if not repo_name:
                            continue

                        repo_short_name = (
                            repo_name.split("/")[-1] if "/" in repo_name else repo_name
                        )

                        try:
                            artifacts = await self.get_artifacts(project_name, repo_short_name)
                            canonical_names = self.generate_canonical_names(
                                harbor_host, project_name, repo_short_name, artifacts
                            )
                            all_canonical_names.extend(canonical_names)

                        except Exception as e:
                            self._logger.error(
                                f"Failed to process repository {repo_short_name}: {e}"
                            )
                            continue

                except Exception as e:
                    self._logger.error(f"Failed to process project {project_name}: {e}")
                    continue

        except Exception as e:
            self._logger.error(f"Failed to fetch projects: {e}")

        return all_canonical_names

    async def scan_specific_registry(self, project_name: str) -> list[str]:
        harbor_host = self._registry_url.replace("http://", "").replace("https://", "")
        all_canonical_names = []

        try:
            repositories = await self.get_repositories(project_name)

            for repository in repositories:
                repo_name = repository.get("name", "")
                if not repo_name:
                    continue

                repo_short_name = repo_name.split("/")[-1] if "/" in repo_name else repo_name

                try:
                    artifacts = await self.get_artifacts(project_name, repo_short_name)
                    canonical_names = self.generate_canonical_names(
                        harbor_host, project_name, repo_short_name, artifacts
                    )
                    all_canonical_names.extend(canonical_names)

                except Exception as e:
                    self._logger.error(f"Failed to process repository {repo_short_name}: {e}")
                    continue

        except Exception as e:
            self._logger.error(f"Failed to process project {project_name}: {e}")

        return all_canonical_names
