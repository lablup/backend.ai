"""The audit log adapter, assembled for one row.

The only place in the audit-log scenarios that knows how the adapter is built. What it is
built with — the validators the row's config settles, the recorder — comes from the root
conftest. The adapter has no external dependency; its records come from the database.
"""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.audit_log import AuditLogFieldType
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import FieldGroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.audit_log.adapter import AuditLogAdapter
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.services.audit_log.processors import AuditLogProcessors


@pytest.fixture
async def adapter(
    engine: Any,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> AuditLogAdapter:
    provider = V2DBOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(provider),
        )
    )
    return AuditLogAdapter(
        AuditLogProcessors(
            registry.dangling_field_group(FieldGroupMeta(AuditLogFieldType()), AuditLogData)
        )
    )
