"""Tests for the registry config check the v2 write path runs.

`ContainerRegistryRepository._validate_config` holds the same rules as
`ContainerRegistryValidator` in `models/container_registry/row.py`, which api/gql_legacy
runs. The legacy copy is covered by `tests/unit/manager/api/test_container_registry_validator.py`;
this covers the v2 one, so the two cannot drift unnoticed.
"""

from __future__ import annotations

import uuid

import pytest

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.errors.container_registry import (
    InvalidContainerRegistryProject,
    InvalidContainerRegistryURL,
)
from ai.backend.manager.repositories.container_registry.repository import (
    ContainerRegistryRepository,
)


def _data(
    *,
    url: str,
    registry_type: ContainerRegistryType,
    project: str | None,
) -> ContainerRegistryData:
    return ContainerRegistryData(
        id=ContainerRegistryID(uuid.uuid4()),
        url=url,
        registry_name="registry",
        type=registry_type,
        project=project,
        username=None,
        password=None,
        ssl_verify=None,
        is_global=False,
        extra=None,
    )


class TestValidateConfig:
    @pytest.mark.parametrize(
        "url",
        [
            "https://registry.example.com",
            "http://registry.example.com:5000",
            "registry.example.com",
            "  https://registry.example.com  ",
        ],
    )
    def test_accepts_urls_with_a_host(self, url: str) -> None:
        """A URL is accepted once a host can be read out of it, with or without a scheme."""
        ContainerRegistryRepository._validate_config(
            _data(url=url, registry_type=ContainerRegistryType.DOCKER, project=None)
        )

    @pytest.mark.parametrize("url", ["", "   ", "https://", "http://"])
    def test_rejects_urls_without_a_host(self, url: str) -> None:
        """A URL carrying no host is rejected."""
        with pytest.raises(InvalidContainerRegistryURL):
            ContainerRegistryRepository._validate_config(
                _data(url=url, registry_type=ContainerRegistryType.DOCKER, project=None)
            )

    @pytest.mark.parametrize(
        "registry_type",
        [ContainerRegistryType.HARBOR, ContainerRegistryType.HARBOR2],
    )
    def test_harbor_requires_a_project(self, registry_type: ContainerRegistryType) -> None:
        """Both Harbor variants refuse a registry that names no project."""
        with pytest.raises(InvalidContainerRegistryProject):
            ContainerRegistryRepository._validate_config(
                _data(
                    url="https://registry.example.com",
                    registry_type=registry_type,
                    project=None,
                )
            )

    @pytest.mark.parametrize("project", ["lowercase", "under_score-ok.dot", "proj1"])
    def test_harbor_accepts_lowercase_project_names(self, project: str) -> None:
        """A Harbor project name takes lowercase segments joined by one separator."""
        ContainerRegistryRepository._validate_config(
            _data(
                url="https://registry.example.com",
                registry_type=ContainerRegistryType.HARBOR2,
                project=project,
            )
        )

    @pytest.mark.parametrize("project", ["", "Upper", "-lead", "trail-", "two__seps"])
    def test_harbor_rejects_malformed_project_names(self, project: str) -> None:
        """An empty name, an uppercase letter or a stray separator is rejected."""
        with pytest.raises(InvalidContainerRegistryProject):
            ContainerRegistryRepository._validate_config(
                _data(
                    url="https://registry.example.com",
                    registry_type=ContainerRegistryType.HARBOR2,
                    project=project,
                )
            )

    def test_harbor_rejects_a_project_name_over_255_characters(self) -> None:
        """A Harbor project name longer than 255 characters is rejected."""
        with pytest.raises(InvalidContainerRegistryProject):
            ContainerRegistryRepository._validate_config(
                _data(
                    url="https://registry.example.com",
                    registry_type=ContainerRegistryType.HARBOR2,
                    project="a" * 256,
                )
            )

    def test_docker_ignores_the_project(self) -> None:
        """A non-Harbor registry takes any project name, including none."""
        ContainerRegistryRepository._validate_config(
            _data(
                url="https://registry.example.com",
                registry_type=ContainerRegistryType.DOCKER,
                project="Anything Goes",
            )
        )
