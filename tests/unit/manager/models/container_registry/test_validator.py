from __future__ import annotations

import pytest

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.manager.errors.container_registry import (
    InvalidContainerRegistryProject,
    InvalidContainerRegistryURL,
)
from ai.backend.manager.models.container_registry.validator import (
    ContainerRegistryValidator,
    ContainerRegistryValidatorArgs,
)


class TestContainerRegistryValidator:
    """Tests for the validator the v2 repository path runs."""

    @pytest.mark.parametrize(
        "url",
        [
            "https://registry.example.com",
            "http://registry.example.com:5000",
            "registry.example.com",
            "  https://registry.example.com  ",
        ],
    )
    async def test_accepts_urls_with_a_host(self, url: str) -> None:
        """A URL is accepted once a host can be read out of it, with or without a scheme."""
        args = ContainerRegistryValidatorArgs(
            url=url, type=ContainerRegistryType.DOCKER, project=None
        )

        ContainerRegistryValidator(args).validate()

    @pytest.mark.parametrize("url", ["", "   ", "https://", "http://"])
    async def test_rejects_urls_without_a_host(self, url: str) -> None:
        """A URL carrying no host is rejected."""
        args = ContainerRegistryValidatorArgs(
            url=url, type=ContainerRegistryType.DOCKER, project=None
        )

        with pytest.raises(InvalidContainerRegistryURL):
            ContainerRegistryValidator(args).validate()

    @pytest.mark.parametrize(
        "registry_type",
        [ContainerRegistryType.HARBOR, ContainerRegistryType.HARBOR2],
    )
    async def test_harbor_requires_a_project(self, registry_type: ContainerRegistryType) -> None:
        """Both Harbor variants refuse a registry that names no project."""
        args = ContainerRegistryValidatorArgs(
            url="https://registry.example.com", type=registry_type, project=None
        )

        with pytest.raises(InvalidContainerRegistryProject):
            ContainerRegistryValidator(args).validate()

    @pytest.mark.parametrize("project", ["lowercase", "under_score-ok.dot", "proj1"])
    async def test_harbor_accepts_lowercase_project_names(self, project: str) -> None:
        """A Harbor project name takes lowercase segments joined by one separator."""
        args = ContainerRegistryValidatorArgs(
            url="https://registry.example.com",
            type=ContainerRegistryType.HARBOR2,
            project=project,
        )

        ContainerRegistryValidator(args).validate()

    @pytest.mark.parametrize("project", ["", "Upper", "-lead", "trail-", "two__seps"])
    async def test_harbor_rejects_malformed_project_names(self, project: str) -> None:
        """An empty name, an uppercase letter or a stray separator is rejected."""
        args = ContainerRegistryValidatorArgs(
            url="https://registry.example.com",
            type=ContainerRegistryType.HARBOR2,
            project=project,
        )

        with pytest.raises(InvalidContainerRegistryProject):
            ContainerRegistryValidator(args).validate()

    async def test_harbor_project_length(self) -> None:
        """A Harbor project name longer than 255 characters is rejected."""
        args = ContainerRegistryValidatorArgs(
            url="https://registry.example.com",
            type=ContainerRegistryType.HARBOR2,
            project="a" * 256,
        )

        with pytest.raises(InvalidContainerRegistryProject):
            ContainerRegistryValidator(args).validate()

    async def test_docker_ignores_the_project(self) -> None:
        """A non-Harbor registry takes any project name, including none."""
        args = ContainerRegistryValidatorArgs(
            url="https://registry.example.com",
            type=ContainerRegistryType.DOCKER,
            project="Anything Goes",
        )

        ContainerRegistryValidator(args).validate()
