from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ai.backend.common.dependencies import NonMonitorableDependencyProvider, ResourceT
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.manager.config.unified import PluginsConfig


@dataclass
class PluginsInput:
    """Input required for plugin context setup."""

    etcd: AsyncEtcd
    local_config: Mapping[str, Any]
    plugins_config: PluginsConfig
    allowed_plugins: set[str] | None
    disabled_plugins: set[str] | None
    init_context: Any | None = None


class PluginDependency(NonMonitorableDependencyProvider[PluginsInput, ResourceT]):
    """Base class for plugin context dependencies."""

    pass
