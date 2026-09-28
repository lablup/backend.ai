"""Shared setup for fair-share repository tests.

A few tests here instantiate ORM rows (``DomainFairShareRow`` and friends) and
call ``to_data()`` directly. Instantiating a mapped class makes SQLAlchemy
configure every imported mapper and resolve string-based ``relationship()``
targets. Those targets are imported only under ``TYPE_CHECKING`` in the model
modules, so they have to be imported (and registered) here.

Following the repository test convention, the related rows are imported in FK
order and handed to ``with_tables`` via the ``fair_share_row_tables`` fixture;
tests that build rows in-memory request that fixture so the mappers are
configured before construction.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest

from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.fair_share.row import (
    DomainFairShareRow,
    ProjectFairShareRow,
    UserFairShareRow,
)
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import AssocGroupUserRow, ProjectRow
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.resource_group.row import (
    ResourceGroupForDomainRow,
    ResourceGroupForProjectRow,
    ResourceGroupRow,
)
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.models.resource_slot.row import AgentResourceRow, ResourceSlotTypeRow
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.db import with_tables


@pytest.fixture
async def fair_share_row_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    """Create the fair-share tables and register the related ORM mappers.

    Rows are listed in FK dependency order (parents before children); the
    relationship targets (e.g. ``ResourceGroupForDomainRow``) must be present so
    SQLAlchemy can configure the ``DomainFairShareRow`` / ``ProjectFairShareRow``
    / ``UserFairShareRow`` mappers.
    """
    async with with_tables(
        database_connection,
        [
            # Base rows in FK dependency order (parents before children)
            DomainRow,
            ResourceGroupRow,
            ResourceGroupForDomainRow,
            UserResourcePolicyRow,
            ProjectResourcePolicyRow,
            KeyPairResourcePolicyRow,
            RoleRow,
            UserRoleRow,
            UserRow,
            KeyPairRow,
            ProjectRow,
            ResourceGroupForProjectRow,
            AssocGroupUserRow,
            AgentRow,
            ContainerRegistryRow,
            ImageRow,
            SessionRow,
            KernelRow,
            ResourcePresetRow,
            ResourceSlotTypeRow,
            AgentResourceRow,
            # Fair Share rows (no FK constraints but need mapper registration)
            DomainFairShareRow,
            ProjectFairShareRow,
            UserFairShareRow,
        ],
    ):
        yield database_connection
