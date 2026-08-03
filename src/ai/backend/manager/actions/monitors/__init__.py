from dataclasses import dataclass, field

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.v2.bulk.monitor.base import BulkActionMonitor
from ai.backend.manager.actions.v2.global_scope.monitor.base import GlobalActionMonitor
from ai.backend.manager.actions.v2.scope.monitor.base import ScopeActionMonitor
from ai.backend.manager.actions.v2.single_entity.monitor.base import SingleEntityActionMonitor

__all__ = ("ActionMonitors",)


@dataclass
class ActionMonitors:
    """Monitors grouped per action framework, mirroring :class:`ActionValidators`.

    ``legacy`` feeds the ``BaseAction``-era processors; the per-type fields feed
    the v2 processors (``actions/v2/``).
    """

    legacy: list[ActionMonitor] = field(default_factory=list)
    single_entity: list[SingleEntityActionMonitor] = field(default_factory=list)
    bulk: list[BulkActionMonitor] = field(default_factory=list)
    scope: list[ScopeActionMonitor] = field(default_factory=list)
    global_scope: list[GlobalActionMonitor] = field(default_factory=list)
