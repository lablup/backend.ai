from __future__ import annotations

from typing import Generic

from ai.backend.common.dependencies import DependencyProvider, ResourceT
from ai.backend.manager.config.unified import ManagerUnifiedConfig


class InfrastructureDependency(
    DependencyProvider[ManagerUnifiedConfig, ResourceT], Generic[ResourceT]
):
    """Base class for infrastructure dependencies that only need ManagerUnifiedConfig.

    Infrastructure dependencies are foundational resources (etcd, redis, database)
    that can be initialized solely from the manager's unified configuration.
    """

    pass
