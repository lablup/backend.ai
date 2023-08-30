from __future__ import annotations

from typing import TYPE_CHECKING, Any, Mapping, Type

import yarl

if TYPE_CHECKING:
    from .base import BaseContainerRegistry


def get_container_registry_cls(registry_info: Mapping[str, Any]) -> Type[BaseContainerRegistry]:
    registry_url = yarl.URL(registry_info[""])
    registry_type = registry_info.get("type", "docker")
    cr_cls: Type[BaseContainerRegistry]
    if registry_url.host is not None and registry_url.host.endswith(".docker.io"):
        from .docker import DockerHubRegistry

        cr_cls = DockerHubRegistry
    elif registry_type == "docker":
        from .docker import DockerRegistry_v2

        cr_cls = DockerRegistry_v2
    elif registry_type == "harbor":
        from .harbor import HarborRegistry_v1

        cr_cls = HarborRegistry_v1
    elif registry_type == "harbor2":
        from .harbor import HarborRegistry_v2

        cr_cls = HarborRegistry_v2
    elif registry_type == "local":
        from .local import LocalRegistry

        cr_cls = LocalRegistry
    else:
        raise RuntimeError(f"Unsupported registry type: {registry_type}")
    return cr_cls
