from __future__ import annotations

from typing import TYPE_CHECKING, Type

import yarl

from ai.backend.manager.models.container_registry import ContainerRegistryRow, ContainerRegistryType

if TYPE_CHECKING:
    from .base import BaseContainerRegistry


def get_container_registry_cls(registry_info: ContainerRegistryRow) -> Type[BaseContainerRegistry]:
    registry_url = yarl.URL(registry_info.url)
    registry_type = registry_info.type
    cr_cls: Type[BaseContainerRegistry]
    if registry_url.host is not None and registry_url.host.endswith(".docker.io"):
        from .docker import DockerHubRegistry

        cr_cls = DockerHubRegistry
    elif registry_type == ContainerRegistryType.DOCKER:
        from .docker import DockerRegistry_v2

        cr_cls = DockerRegistry_v2
    elif registry_type == ContainerRegistryType.HARBOR:
        from .harbor import HarborRegistry_v1

        cr_cls = HarborRegistry_v1
    elif registry_type == ContainerRegistryType.HARBOR2:
        from .harbor import HarborRegistry_v2

        cr_cls = HarborRegistry_v2
    elif registry_type == ContainerRegistryType.GITHUB:
        from .github import GitHubRegistry

        cr_cls = GitHubRegistry
    elif registry_type == ContainerRegistryType.GITLAB:
        from .gitlab import GitLabRegistry

        cr_cls = GitLabRegistry
    elif registry_type in [ContainerRegistryType.ECR, ContainerRegistryType.ECR_PUB]:
        from .aws_ecr import AWSElasticContainerRegistry

        cr_cls = AWSElasticContainerRegistry
    elif registry_type == ContainerRegistryType.LOCAL:
        from .local import LocalRegistry

        cr_cls = LocalRegistry
    else:
        raise RuntimeError(f"Unsupported registry type: {registry_type}")
    return cr_cls
