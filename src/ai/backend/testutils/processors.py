"""Processor wiring for tests that drive ops-direct domains against a real DB.

An ops-direct domain takes a :class:`ProcessorGroup` instead of a repository and a
validator bundle. Assembling it here means a change to :class:`ProcessorDependencies`
lands in one place rather than in every conftest.
"""

from typing import Any

from ai.backend.common.data.entity.types import FieldData
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.field import FieldGroup
from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import (
    FieldGroupMeta,
    GroupMeta,
    ProcessorDependencies,
)
from ai.backend.manager.actions.v2.validators import ActionValidators
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider


def ops_processor_group(db: ExtendedAsyncSAEngine, meta: GroupMeta) -> ProcessorGroup[Any]:
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
    ).group(meta)


def ops_field_group[TFieldData: FieldData](
    db: ExtendedAsyncSAEngine, meta: FieldGroupMeta, data_cls: type[TFieldData]
) -> FieldGroup[TFieldData]:
    """The field-row counterpart of :func:`ops_processor_group`, for a field kind whose
    owner is not fixed."""
    return ProcessorRegistry(
        ProcessorDependencies(
            monitors=ActionMonitors(),
            validators=ActionValidators(),
            repository=OpsRepository(V2DBOpsProvider(db)),
        )
    ).dangling_field_group(meta, data_cls)
