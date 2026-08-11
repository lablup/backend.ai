"""Processor wiring for tests that drive ops-direct domains against a real DB.

A domain migrated to ops-generic wiring takes a :class:`ProcessorGroup` instead of a
repository and a validator bundle, so every test that builds its processors by hand has
to know how that group is assembled. Keeping that knowledge here means a change to
:class:`ProcessorDependencies` lands in one place rather than in every conftest.
"""

from typing import Any

from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry import (
    ProcessorDependencies,
    ProcessorGroup,
    ProcessorRegistry,
)
from ai.backend.manager.actions.v2.validators import ActionValidators
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider


def ops_processor_group(db: ExtendedAsyncSAEngine) -> ProcessorGroup[Any]:
    """A processor group backed by the given engine, with no extra monitors or validators.

    The gates a processor imposes on itself still apply — the global processor prepends
    its SUPERADMIN check regardless of what this bundle carries.
    """
    return ProcessorRegistry(
        ProcessorDependencies(
            monitors=ActionMonitors(),
            validators=ActionValidators(),
            repository=OpsRepository(V2DBOpsProvider(db)),
        )
    ).group()
