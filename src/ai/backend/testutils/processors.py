"""Processor wiring for tests that drive ops-direct domains against a real DB.

An ops-direct domain takes a :class:`ProcessorGroup` instead of a repository and a
validator bundle. Assembling it here means a change to :class:`ProcessorDependencies`
lands in one place rather than in every conftest.
"""

from typing import Any

from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import (
    GroupMeta,
    ProcessorDependencies,
)
from ai.backend.manager.actions.v2.validators import ActionValidators
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.testutils.action_validators import build_global_gate


def ops_processor_group(
    db: ExtendedAsyncSAEngine,
    meta: GroupMeta,
    config_provider: ManagerConfigProvider,
) -> ProcessorGroup[Any]:
    """A processor group backed by the given engine, with no extra monitors.

    Callers run global actions through these groups, so the global gate is the
    production one over the same engine: a super admin passes without a read, and
    everyone else is answered by that database's graph.
    """
    return ProcessorRegistry(
        ProcessorDependencies(
            monitors=ActionMonitors(),
            validators=ActionValidators(global_scope=[build_global_gate(db, config_provider)]),
            repository=OpsRepository(V2DBOpsProvider(db)),
        )
    ).group(meta)
