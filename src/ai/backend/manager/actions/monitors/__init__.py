from dataclasses import dataclass, field

from ai.backend.manager.actions.bulk.monitor.base import BulkActionMonitor
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.scope.monitor.base import ScopeActionMonitor
from ai.backend.manager.actions.single_entity.monitor.base import SingleEntityActionMonitor

__all__ = ("ActionMonitors",)


@dataclass
class ActionMonitors:
    """Monitors grouped per action framework, mirroring :class:`ActionValidators`.

    ``legacy`` feeds the ``BaseAction``-era processors; the per-type fields feed
    the pure-ABC processors (``actions/{single_entity,bulk,scope}``).
    """

    legacy: list[ActionMonitor] = field(default_factory=list)
    single_entity: list[SingleEntityActionMonitor] = field(default_factory=list)
    bulk: list[BulkActionMonitor] = field(default_factory=list)
    scope: list[ScopeActionMonitor] = field(default_factory=list)
