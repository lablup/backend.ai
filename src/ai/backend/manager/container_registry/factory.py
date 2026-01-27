from __future__ import annotations

from typing import TYPE_CHECKING

import yarl

from ai.backend.common.container_registry import ContainerRegistryType

if TYPE_CHECKING:
    from ai.backend.manager.models.container_registry import ContainerRegistryRow

    from .base import BaseContainerRegistry


def get_container_registry_cls(registry_info: ContainerRegistryRow) -> type[BaseContainerRegistry]:
    registry_url = yarl.URL(registry_info.url)
    registry_type = registry_info.type

    # Check for DockerHub first (by URL pattern)
    if registry_url.host is not None and registry_url.host.endswith(".docker.io"):
        from .docker import DockerHubRegistry

        return DockerHubRegistry

    # Match by registry type
    match registry_type:
        case ContainerRegistryType.DOCKER:
            from .docker import DockerRegistry_v2

            return DockerRegistry_v2
        case ContainerRegistryType.HARBOR:
            from .harbor import HarborRegistry_v1

            return HarborRegistry_v1
        case ContainerRegistryType.HARBOR2:
            from .harbor import HarborRegistry_v2

            return HarborRegistry_v2
        case ContainerRegistryType.GITHUB:
            from .github import GitHubRegistry

            return GitHubRegistry
        case ContainerRegistryType.GITLAB:
            from .gitlab import GitLabRegistry

            return GitLabRegistry
        case ContainerRegistryType.ECR | ContainerRegistryType.ECR_PUB:
            from .aws_ecr import AWSElasticContainerRegistry

            return AWSElasticContainerRegistry
        case ContainerRegistryType.LOCAL:
            from .local import LocalRegistry

            return LocalRegistry
        case ContainerRegistryType.OCP:
            from .ocp import OpenShiftPlatformContainerRegistry

            return OpenShiftPlatformContainerRegistry
        case _:
            raise RuntimeError(f"Unsupported registry type: {registry_type}")
