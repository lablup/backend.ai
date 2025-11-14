from __future__ import annotations

from typing import Generic

from ai.backend.common.dependencies import DependencyProvider, ResourceT
from ai.backend.common.etcd import AsyncEtcd


class ConfigDependency(DependencyProvider[AsyncEtcd, ResourceT], Generic[ResourceT]):
    """Base class for config dependencies that require etcd client."""

    pass
