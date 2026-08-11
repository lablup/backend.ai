"""Integration tests for the resource slot type creator/updater/purger specs."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from decimal import Decimal

import pytest
import sqlalchemy as sa

from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import ResourceSlot, SlotTypes
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.errors.resource_slot import (
    ResourceSlotTypeAlreadyExists,
    ResourceSlotTypeInUse,
)
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_slot.creators import ResourceSlotTypeCreator
from ai.backend.manager.models.resource_slot.purgers import ResourceSlotTypePurger
from ai.backend.manager.models.resource_slot.row import (
    AgentResourceRow,
    DeploymentRevisionResourceSlotRow,
    ModelCardResourceRequirementRow,
    PresetResourceSlotRow,
    ResourceAllocationRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.resource_slot.types import NumberFormat
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.runtime_variant import RuntimeVariantRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.resource_slot.updaters import ResourceSlotTypeUpdater
from ai.backend.manager.types import OptionalState
from ai.backend.testutils.db import with_tables


@pytest.fixture
async def db_with_referencing_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    """Every table the purger's conflict checks read, plus their FK parents.

    The conflict checks are validated in one query spanning all five referencing
    tables, so each of them has to exist even when only one carries a row.
    """
    async with with_tables(
        database_connection,
        [
            DomainRow,
            ScalingGroupRow,
            UserResourcePolicyRow,
            ProjectResourcePolicyRow,
            KeyPairResourcePolicyRow,
            RoleRow,
            UserRoleRow,
            UserRow,
            KeyPairRow,
            GroupRow,
            AgentRow,
            ContainerRegistryRow,
            ImageRow,
            VFolderRow,
            EndpointRow,
            ReplicaGroupRow,
            RuntimeVariantRow,
            DeploymentRevisionPresetRow,
            DeploymentRevisionRow,
            SessionRow,
            KernelRow,
            RoutingRow,
            ModelCardRow,
            AssociationScopesEntitiesRow,
            ResourceSlotTypeRow,
            AgentResourceRow,
            ResourceAllocationRow,
            ModelCardResourceRequirementRow,
            PresetResourceSlotRow,
            DeploymentRevisionResourceSlotRow,
        ],
    ):
        yield database_connection


@pytest.fixture
async def existing_slot_type(
    db_with_referencing_tables: ExtendedAsyncSAEngine,
) -> str:
    slot_name = "cuda.device"
    async with db_with_referencing_tables.begin_session() as db_sess:
        db_sess.add(
            ResourceSlotTypeRow(
                slot_name=slot_name,
                slot_type="unique",
                display_name="GPU",
                rank=3,
            )
        )
    return slot_name


def _creator(
    slot_name: str,
    slot_type: SlotTypes,
    *,
    required: bool = False,
    enabled: bool = True,
    display_name: str = "",
    rank: int = 0,
) -> ResourceSlotTypeCreator:
    """Build a creator with every field named, since the spec carries no defaults."""
    return ResourceSlotTypeCreator(
        slot_name=slot_name,
        slot_type=slot_type,
        required=required,
        enabled=enabled,
        display_name=display_name,
        description="",
        display_unit="",
        display_icon="",
        number_format=NumberFormat(),
        rank=rank,
    )


class TestResourceSlotTypeCreator:
    async def test_insert_returns_stored_values(
        self,
        db_with_referencing_tables: ExtendedAsyncSAEngine,
    ) -> None:
        creator = _creator(
            "tpu.device",
            SlotTypes.UNIQUE,
            required=True,
            enabled=False,
            display_name="TPU",
            rank=7,
        )
        async with V2DBOpsProvider(db_with_referencing_tables).write_ops() as w:
            data = await w.create_global_entity(creator)

        assert data.slot_name == "tpu.device"
        assert data.slot_type == "unique"
        assert data.required is True
        assert data.enabled is False
        assert data.rank == 7
        assert isinstance(data.uuid, uuid.UUID)

    async def test_each_row_gets_a_distinct_uuid(
        self,
        db_with_referencing_tables: ExtendedAsyncSAEngine,
    ) -> None:
        uuids = set()
        for name in ("cpu", "mem"):
            creator = _creator(name, SlotTypes.COUNT)
            async with V2DBOpsProvider(db_with_referencing_tables).write_ops() as w:
                data = await w.create_global_entity(creator)
                uuids.add(data.uuid)
        assert len(uuids) == 2

    async def test_existing_name_conflicts_and_leaves_the_row_alone(
        self,
        db_with_referencing_tables: ExtendedAsyncSAEngine,
        existing_slot_type: str,
    ) -> None:
        creator = _creator(
            existing_slot_type,
            SlotTypes.COUNT,
            display_name="Overwritten",
        )
        with pytest.raises(ResourceSlotTypeAlreadyExists):
            async with V2DBOpsProvider(db_with_referencing_tables).write_ops() as w:
                await w.create_global_entity(creator)

        async with db_with_referencing_tables.begin_readonly_session() as db_sess:
            row = await db_sess.scalar(
                sa.select(ResourceSlotTypeRow).where(
                    ResourceSlotTypeRow.slot_name == existing_slot_type
                )
            )
            assert row is not None
            assert row.slot_type == "unique"
            assert row.display_name == "GPU"


class TestResourceSlotTypeUpdater:
    async def test_updates_only_the_named_fields(
        self,
        db_with_referencing_tables: ExtendedAsyncSAEngine,
        existing_slot_type: str,
    ) -> None:
        updater = ResourceSlotTypeUpdater(
            slot_name=existing_slot_type,
            enabled=OptionalState.update(False),
            required=OptionalState.update(True),
        )
        provider = V2DBOpsProvider(db_with_referencing_tables)
        async with provider.write_ops() as w:
            data_or_none = await w.update_data(updater)
        assert data_or_none is not None
        data = data_or_none

        assert data.enabled is False
        assert data.required is True
        assert data.display_name == "GPU"
        assert data.slot_type == "unique"

    async def test_unknown_name_matches_nothing(
        self,
        db_with_referencing_tables: ExtendedAsyncSAEngine,
    ) -> None:
        updater = ResourceSlotTypeUpdater(
            slot_name="no.such.slot",
            enabled=OptionalState.update(False),
        )
        provider = V2DBOpsProvider(db_with_referencing_tables)
        async with provider.write_ops() as w:
            assert await w.update_data(updater) is None


class TestResourceSlotTypePurger:
    async def test_removes_an_unreferenced_slot_type(
        self,
        db_with_referencing_tables: ExtendedAsyncSAEngine,
        existing_slot_type: str,
    ) -> None:
        purger = ResourceSlotTypePurger(slot_name=existing_slot_type)
        async with V2DBOpsProvider(db_with_referencing_tables).write_ops() as w:
            data = await w.purge_global_entity(purger)
            assert data is not None
            assert data.slot_name == existing_slot_type

        async with db_with_referencing_tables.begin_readonly_session() as db_sess:
            remaining = await db_sess.scalar(
                sa.select(sa.func.count())
                .select_from(ResourceSlotTypeRow)
                .where(ResourceSlotTypeRow.slot_name == existing_slot_type)
            )
            assert remaining == 0

    async def test_refuses_while_an_agent_reports_the_slot(
        self,
        db_with_referencing_tables: ExtendedAsyncSAEngine,
        existing_slot_type: str,
    ) -> None:
        agent_id = "i-conflict"
        resource_group_id = ResourceGroupID(uuid.uuid4())
        async with db_with_referencing_tables.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    id=DomainID(uuid.uuid4()),
                    name="conflict-domain",
                    total_resource_slots=ResourceSlot(),
                )
            )
            db_sess.add(
                ScalingGroupRow(
                    id=resource_group_id,
                    name="conflict-sgroup",
                    driver="static",
                    scheduler="fifo",
                    scheduler_opts=ScalingGroupOpts(),
                )
            )
            await db_sess.flush()
            db_sess.add(
                AgentRow(
                    id=agent_id,
                    status=AgentStatus.ALIVE,
                    region="local",
                    version="26.9.0",
                    scaling_group="conflict-sgroup",
                    resource_group_id=resource_group_id,
                    available_slots=ResourceSlot(),
                    occupied_slots=ResourceSlot(),
                    addr="tcp://127.0.0.1:6011",
                    architecture="x86_64",
                )
            )
            await db_sess.flush()
            db_sess.add(
                AgentResourceRow(
                    agent_id=agent_id,
                    slot_name=existing_slot_type,
                    capacity=Decimal(2),
                )
            )

        purger = ResourceSlotTypePurger(slot_name=existing_slot_type)
        with pytest.raises(ResourceSlotTypeInUse):
            async with V2DBOpsProvider(db_with_referencing_tables).write_ops() as w:
                await w.purge_global_entity(purger)

        async with db_with_referencing_tables.begin_readonly_session() as db_sess:
            remaining = await db_sess.scalar(
                sa.select(sa.func.count())
                .select_from(ResourceSlotTypeRow)
                .where(ResourceSlotTypeRow.slot_name == existing_slot_type)
            )
            assert remaining == 1
