from __future__ import annotations

from typing import Annotated

from pydantic import Field

from ai.backend.common.config import BaseConfigSchema
from ai.backend.common.meta import BackendAIConfigMeta, ConfigExample
from ai.backend.common.types import ServiceDiscoveryType

__all__ = ("ServiceDiscoveryConfig",)


class ServiceDiscoveryConfig(BaseConfigSchema):
    """Configuration for service discovery mechanism.

    Service discovery allows Backend.AI components to locate and communicate
    with each other in a distributed environment.
    """

    type: Annotated[
        ServiceDiscoveryType,
        Field(default=ServiceDiscoveryType.REDIS),
        BackendAIConfigMeta(
            description=(
                "Type of service discovery to use. Supported types are 'etcd' and 'redis'."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="redis", prod="redis"),
        ),
    ]
