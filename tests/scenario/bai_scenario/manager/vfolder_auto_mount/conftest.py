"""The vfolder auto-mount adapter, assembled for one row."""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.vfolder_auto_mount import VFolderAutoMountEntityType
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.vfolder_auto_mount.adapter import VFolderAutoMountAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.vfolder_auto_mount.repository import (
    VFolderAutoMountRepository,
)
from ai.backend.manager.services.vfolder_auto_mount.processors import VFolderAutoMountProcessors
from ai.backend.manager.services.vfolder_auto_mount.service import VFolderAutoMountService


@pytest.fixture
async def adapter(
    engine: ExtendedAsyncSAEngine,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> VFolderAutoMountAdapter:
    provider = V2DBOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(provider),
        )
    )
    service = VFolderAutoMountService(VFolderAutoMountRepository(provider))
    return VFolderAutoMountAdapter(
        VFolderAutoMountProcessors(registry.group(GroupMeta(VFolderAutoMountEntityType())), service)
    )
