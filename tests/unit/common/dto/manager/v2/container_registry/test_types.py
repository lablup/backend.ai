"""Tests for ai.backend.common.dto.manager.v2.container_registry.types module."""

from __future__ import annotations

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.dto.manager.v2.container_registry.types import (
    ContainerRegistryType as ExportedContainerRegistryType,
)


class TestContainerRegistryTypeReExport:
    """Tests verifying ContainerRegistryType is properly re-exported from types module."""

    def test_is_same_object(self) -> None:
        assert ExportedContainerRegistryType is ContainerRegistryType

    def test_docker_value(self) -> None:
        assert ExportedContainerRegistryType.DOCKER.value == "docker"

    def test_harbor_value(self) -> None:
        assert ExportedContainerRegistryType.HARBOR.value == "harbor"

    def test_harbor2_value(self) -> None:
        assert ExportedContainerRegistryType.HARBOR2.value == "harbor2"

    def test_github_value(self) -> None:
        assert ExportedContainerRegistryType.GITHUB.value == "github"

    def test_gitlab_value(self) -> None:
        assert ExportedContainerRegistryType.GITLAB.value == "gitlab"

    def test_all_values_are_strings(self) -> None:
        for member in ExportedContainerRegistryType:
            assert isinstance(member.value, str)

    def test_from_string_docker(self) -> None:
        assert ExportedContainerRegistryType("docker") is ContainerRegistryType.DOCKER

    def test_from_string_harbor(self) -> None:
        assert ExportedContainerRegistryType("harbor") is ContainerRegistryType.HARBOR

    def test_from_string_github(self) -> None:
        assert ExportedContainerRegistryType("github") is ContainerRegistryType.GITHUB

    def test_from_string_gitlab(self) -> None:
        assert ExportedContainerRegistryType("gitlab") is ContainerRegistryType.GITLAB
