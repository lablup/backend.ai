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

from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.fair_share import (
    DomainFairShareRow,
    ProjectFairShareRow,
    UserFairShareRow,
)
from ai.backend.manager.models.group import AssocGroupUserRow, GroupRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.resource_slot import AgentResourceRow, ResourceSlotTypeRow
from ai.backend.manager.models.scaling_group import (
    ScalingGroupForDomainRow,
    ScalingGroupForProjectRow,
    ScalingGroupRow,
)
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.db import with_tables


@pytest.fixture
async def fair_share_row_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    """Create the fair-share tables and register the related ORM mappers.

    Rows are listed in FK dependency order (parents before children); the
    relationship targets (e.g. ``ScalingGroupForDomainRow``) must be present so
    SQLAlchemy can configure the ``DomainFairShareRow`` / ``ProjectFairShareRow``
    / ``UserFairShareRow`` mappers.
    """
    async with with_tables(
        database_connection,
        [
            # Base rows in FK dependency order (parents before children)
            DomainRow,
            ScalingGroupRow,
            ScalingGroupForDomainRow,
            UserResourcePolicyRow,
            ProjectResourcePolicyRow,
            KeyPairResourcePolicyRow,
            RoleRow,
            UserRoleRow,
            UserRow,
            KeyPairRow,
            GroupRow,
            ScalingGroupForProjectRow,
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
