"""The registry settings check only api/gql_legacy runs.

The v2 path validates the url in its request DTO and leaves the Harbor project rule to
`ck_container_registries_harbor_project`, so nothing here is reached from it. gql_legacy
takes neither route; delete this file together with gql_legacy.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.exception import InvalidContainerRegistryURL
from ai.backend.manager.errors.container_registry import InvalidContainerRegistryProject

__all__ = (
    "ContainerRegistryValidator",
    "ContainerRegistryValidatorArgs",
)


@dataclass
class ContainerRegistryValidatorArgs:
    url: str
    type: ContainerRegistryType
    project: str | None


# TODO: Refactor this using inheritance
class ContainerRegistryValidator:
    """
    Validator for container registry configuration.
    """

    _url: str
    _type: ContainerRegistryType
    _project: str | None

    def __init__(self, args: ContainerRegistryValidatorArgs) -> None:
        self._url = args.url
        self._type = args.type
        self._project = args.project

    def _is_valid_url(self, url: str) -> bool:
        try:
            url = url.strip()
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "http://" + url
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def validate(self) -> None:
        """
        Validate container registry configuration.
        """
        # Validate URL format
        if not self._is_valid_url(self._url):
            raise InvalidContainerRegistryURL(f"Invalid URL format: {self._url}")

        # Validate project name for Harbor
        match self._type:
            case ContainerRegistryType.HARBOR | ContainerRegistryType.HARBOR2:
                if self._project is None:
                    raise InvalidContainerRegistryProject("Project name is required for Harbor.")
                if not (1 <= len(self._project) <= 255):
                    raise InvalidContainerRegistryProject("Invalid project name length.")
                pattern = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
                if not pattern.match(self._project):
                    raise InvalidContainerRegistryProject("Invalid project name format.")
            case _:
                pass
