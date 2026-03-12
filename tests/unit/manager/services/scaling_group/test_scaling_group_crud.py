"""Unit tests for Scaling Group CRUD and domain/keypair associations.

Tests create, modify, purge operations through the service/processor layer with
a real database.  Association add/remove/check operations are also tested here.

The scaling group has no REST API v2 endpoints (only legacy GraphQL), so these
service-direct tests cannot be expressed as SDK tests and live here instead of
tests/component/.

Covers scenarios from:
- scaling_group/crud.md (S-CREATE-*, S-MOD-*, S-PURGE-*)
- scaling_group/domain_association.md (S-1 through S-5)
- scaling_group/keypair_association.md (S-1 through S-5)
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.types import AccessKey
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.scaling_group.types import ScalingGroupData
from ai.backend.manager.errors.resource import ScalingGroupNotFound
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.repositories.base.creator import BulkCreator, Creator
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.repositories.base.rbac.scope_binder import (
    RBACScopeBinder,
    RBACScopeBindingPair,
)
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.scaling_group.creators import (
    ScalingGroupCreatorSpec,
    ScalingGroupForDomainCreatorSpec,
    ScalingGroupForKeypairsCreatorSpec,
)
from ai.backend.manager.repositories.scaling_group.purgers import (
    create_scaling_group_for_keypairs_purger,
)
from ai.backend.manager.repositories.scaling_group.repository import ScalingGroupRepository
from ai.backend.manager.repositories.scaling_group.scope_binders import (
    ResourceGroupDomainEntityUnbinder,
)
from ai.backend.manager.repositories.scaling_group.updaters import (
    ScalingGroupDriverConfigUpdaterSpec,
    ScalingGroupMetadataUpdaterSpec,
    ScalingGroupStatusUpdaterSpec,
    ScalingGroupUpdaterSpec,
)
from ai.backend.manager.services.scaling_group.actions.associate_with_domain import (
    AssociateScalingGroupWithDomainsAction,
)
from ai.backend.manager.services.scaling_group.actions.associate_with_keypair import (
    AssociateScalingGroupWithKeypairsAction,
)
from ai.backend.manager.services.scaling_group.actions.create import CreateScalingGroupAction
from ai.backend.manager.services.scaling_group.actions.disassociate_with_domain import (
    DisassociateScalingGroupWithDomainsAction,
)
from ai.backend.manager.services.scaling_group.actions.disassociate_with_keypair import (
    DisassociateScalingGroupWithKeypairsAction,
)
from ai.backend.manager.services.scaling_group.actions.modify import ModifyScalingGroupAction
from ai.backend.manager.services.scaling_group.actions.purge_scaling_group import (
    PurgeScalingGroupAction,
)
from ai.backend.manager.services.scaling_group.processors import ScalingGroupProcessors
from ai.backend.manager.types import OptionalState, TriState

# ---------------------------------------------------------------------------
# Module-level helpers — shared across all test classes
# ---------------------------------------------------------------------------


async def _create_sgroup(
    processors: ScalingGroupProcessors,
    name: str | None = None,
    *,
    driver: str = "static",
    scheduler: str = "fifo",
    is_public: bool = True,
    is_active: bool = True,
    description: str | None = None,
) -> ScalingGroupData:
    """Create a scaling group via the processor."""
    if name is None:
        name = f"test-crud-{uuid.uuid4().hex[:8]}"
    action = CreateScalingGroupAction(
        creator=Creator(
            spec=ScalingGroupCreatorSpec(
                name=name,
                driver=driver,
                scheduler=scheduler,
                is_public=is_public,
                is_active=is_active,
                description=description or f"Test scaling group {name}",
            )
        )
    )
    result = await processors.create_scaling_group.wait_for_complete(action)
    return result.scaling_group


async def _purge_sgroup(
    processors: ScalingGroupProcessors,
    name: str,
) -> None:
    """Purge a scaling group via the processor."""
    action = PurgeScalingGroupAction(purger=Purger(row_class=ScalingGroupRow, pk_value=name))
    await processors.purge_scaling_group.wait_for_complete(action)


class TestScalingGroupCRUD:
    """Full CRUD lifecycle for scaling groups via the processor layer + real DB."""

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    async def test_s_create_1_basic_create_returns_correct_name(
        self,
        scaling_group_processors: ScalingGroupProcessors,
        database_fixture: None,
    ) -> None:
        """S-CREATE-1: superadmin creates a scaling group; result has correct name/driver/scheduler."""
        name = f"crud-create-{uuid.uuid4().hex[:8]}"
        sg = await _create_sgroup(
            scaling_group_processors,
            name,
            driver="static",
            scheduler="fifo",
        )
        try:
            assert isinstance(sg, ScalingGroupData)
            assert sg.name == name
            assert sg.driver.name == "static"
            assert sg.scheduler.name.value == "fifo"
            assert sg.status.is_active is True
            assert sg.status.is_public is True
        finally:
            await _purge_sgroup(scaling_group_processors, name)

    async def test_s_create_3_private_scaling_group(
        self,
        scaling_group_processors: ScalingGroupProcessors,
        database_fixture: None,
    ) -> None:
        """S-CREATE-3: private scaling group (is_public=False) is created correctly."""
        name = f"crud-private-{uuid.uuid4().hex[:8]}"
        sg = await _create_sgroup(
            scaling_group_processors,
            name,
            is_public=False,
        )
        try:
            assert sg.status.is_public is False
        finally:
            await _purge_sgroup(scaling_group_processors, name)

    # ------------------------------------------------------------------
    # MODIFY
    # ------------------------------------------------------------------

    async def test_s_mod_1_modify_description(
        self,
        scaling_group_processors: ScalingGroupProcessors,
        database_fixture: None,
    ) -> None:
        """S-MOD-1: Modify description → updated value returned."""
        name = f"crud-mod-{uuid.uuid4().hex[:8]}"
        await _create_sgroup(scaling_group_processors, name)
        try:
            action = ModifyScalingGroupAction(
                updater=Updater(
                    spec=ScalingGroupUpdaterSpec(
                        metadata=ScalingGroupMetadataUpdaterSpec(
                            description=TriState.update("Updated description"),
                        )
                    ),
                    pk_value=name,
                )
            )
            result = await scaling_group_processors.modify_scaling_group.wait_for_complete(action)
            assert result.scaling_group.metadata.description == "Updated description"
        finally:
            await _purge_sgroup(scaling_group_processors, name)

    async def test_s_mod_2_toggle_public_to_private(
        self,
        scaling_group_processors: ScalingGroupProcessors,
        database_fixture: None,
    ) -> None:
        """S-MOD-2: Toggle is_public from True to False."""
        name = f"crud-mod2-{uuid.uuid4().hex[:8]}"
        sg = await _create_sgroup(scaling_group_processors, name, is_public=True)
        assert sg.status.is_public is True
        try:
            action = ModifyScalingGroupAction(
                updater=Updater(
                    spec=ScalingGroupUpdaterSpec(
                        status=ScalingGroupStatusUpdaterSpec(
                            is_public=OptionalState.update(False),
                        )
                    ),
                    pk_value=name,
                )
            )
            result = await scaling_group_processors.modify_scaling_group.wait_for_complete(action)
            assert result.scaling_group.status.is_public is False
        finally:
            await _purge_sgroup(scaling_group_processors, name)

    async def test_s_mod_3_deactivate_scaling_group(
        self,
        scaling_group_processors: ScalingGroupProcessors,
        database_fixture: None,
    ) -> None:
        """S-MOD-3: Deactivate scaling group (is_active=False)."""
        name = f"crud-mod3-{uuid.uuid4().hex[:8]}"
        await _create_sgroup(scaling_group_processors, name, is_active=True)
        try:
            action = ModifyScalingGroupAction(
                updater=Updater(
                    spec=ScalingGroupUpdaterSpec(
                        status=ScalingGroupStatusUpdaterSpec(
                            is_active=OptionalState.update(False),
                        )
                    ),
                    pk_value=name,
                )
            )
            result = await scaling_group_processors.modify_scaling_group.wait_for_complete(action)
            assert result.scaling_group.status.is_active is False
        finally:
            await _purge_sgroup(scaling_group_processors, name)

    async def test_s_mod_4_change_driver(
        self,
        scaling_group_processors: ScalingGroupProcessors,
        database_fixture: None,
    ) -> None:
        """S-MOD-4: Update driver config."""
        name = f"crud-mod4-{uuid.uuid4().hex[:8]}"
        await _create_sgroup(scaling_group_processors, name, driver="static")
        try:
            action = ModifyScalingGroupAction(
                updater=Updater(
                    spec=ScalingGroupUpdaterSpec(
                        driver=ScalingGroupDriverConfigUpdaterSpec(
                            driver=OptionalState.update("static"),
                            driver_opts=OptionalState.update({"key": "value"}),
                        )
                    ),
                    pk_value=name,
                )
            )
            result = await scaling_group_processors.modify_scaling_group.wait_for_complete(action)
            assert result.scaling_group.driver.name == "static"
        finally:
            await _purge_sgroup(scaling_group_processors, name)

    # ------------------------------------------------------------------
    # PURGE
    # ------------------------------------------------------------------

    async def test_s_purge_1_purge_removes_scaling_group(
        self,
        scaling_group_processors: ScalingGroupProcessors,
        scaling_group_repository: ScalingGroupRepository,
        database_fixture: None,
    ) -> None:
        """S-PURGE-1: Purge a scaling group; it is no longer findable."""
        name = f"crud-purge-{uuid.uuid4().hex[:8]}"
        await _create_sgroup(scaling_group_processors, name)

        action = PurgeScalingGroupAction(purger=Purger(row_class=ScalingGroupRow, pk_value=name))
        result = await scaling_group_processors.purge_scaling_group.wait_for_complete(action)
        assert result.data.name == name

        # Verify it no longer exists
        with pytest.raises(ScalingGroupNotFound):
            await scaling_group_repository.get_scaling_group_by_name(name)


class TestScalingGroupDomainAssociation:
    """Domain association add/remove/check via the processor layer."""

    # ------------------------------------------------------------------
    # S-1: Associate single domain
    # ------------------------------------------------------------------

    async def test_s1_associate_single_domain(
        self,
        scaling_group_processors: ScalingGroupProcessors,
        scaling_group_repository: ScalingGroupRepository,
        domain_fixture: str,
        database_fixture: None,
    ) -> None:
        """S-1: Associate a scaling group with a single domain; association exists in DB."""
        name = f"assoc-dom-{uuid.uuid4().hex[:8]}"
        await _create_sgroup(scaling_group_processors, name)
        try:
            binder = RBACScopeBinder(
                pairs=[
                    RBACScopeBindingPair(
                        spec=ScalingGroupForDomainCreatorSpec(
                            scaling_group=name,
                            domain=domain_fixture,
                        ),
                        entity_ref=RBACElementRef(RBACElementType.RESOURCE_GROUP, name),
                        scope_ref=RBACElementRef(RBACElementType.DOMAIN, domain_fixture),
                    )
                ]
            )
            await scaling_group_processors.associate_scaling_group_with_domains.wait_for_complete(
                AssociateScalingGroupWithDomainsAction(binder=binder)
            )

            exists = await scaling_group_repository.check_scaling_group_domain_association_exists(
                scaling_group=name,
                domain=domain_fixture,
            )
            assert exists is True
        finally:
            await _purge_sgroup(scaling_group_processors, name)

    # ------------------------------------------------------------------
    # S-3: Disassociate domain
    # ------------------------------------------------------------------

    async def test_s3_disassociate_domain_removes_association(
        self,
        scaling_group_processors: ScalingGroupProcessors,
        scaling_group_repository: ScalingGroupRepository,
        domain_fixture: str,
        database_fixture: None,
    ) -> None:
        """S-3: Disassociate domain; check_exists returns False afterwards."""
        name = f"disassoc-dom-{uuid.uuid4().hex[:8]}"
        await _create_sgroup(scaling_group_processors, name)
        try:
            # First associate
            binder = RBACScopeBinder(
                pairs=[
                    RBACScopeBindingPair(
                        spec=ScalingGroupForDomainCreatorSpec(
                            scaling_group=name,
                            domain=domain_fixture,
                        ),
                        entity_ref=RBACElementRef(RBACElementType.RESOURCE_GROUP, name),
                        scope_ref=RBACElementRef(RBACElementType.DOMAIN, domain_fixture),
                    )
                ]
            )
            await scaling_group_processors.associate_scaling_group_with_domains.wait_for_complete(
                AssociateScalingGroupWithDomainsAction(binder=binder)
            )

            # Verify association exists
            assert (
                await scaling_group_repository.check_scaling_group_domain_association_exists(
                    scaling_group=name,
                    domain=domain_fixture,
                )
            ) is True

            # Now disassociate
            unbinder = ResourceGroupDomainEntityUnbinder(
                scaling_groups=[name],
                domain=domain_fixture,
            )
            await (
                scaling_group_processors.disassociate_scaling_group_with_domains.wait_for_complete(
                    DisassociateScalingGroupWithDomainsAction(unbinder=unbinder)
                )
            )

            # Association should be gone
            exists = await scaling_group_repository.check_scaling_group_domain_association_exists(
                scaling_group=name,
                domain=domain_fixture,
            )
            assert exists is False
        finally:
            await _purge_sgroup(scaling_group_processors, name)

    # ------------------------------------------------------------------
    # S-5: Check association existence
    # ------------------------------------------------------------------

    async def test_s5_check_association_existence(
        self,
        scaling_group_processors: ScalingGroupProcessors,
        scaling_group_repository: ScalingGroupRepository,
        domain_fixture: str,
        database_fixture: None,
    ) -> None:
        """S-5: check_scaling_group_domain_association_exists returns True/False correctly."""
        name = f"check-assoc-{uuid.uuid4().hex[:8]}"
        await _create_sgroup(scaling_group_processors, name)
        try:
            # Before association: False
            assert (
                await scaling_group_repository.check_scaling_group_domain_association_exists(
                    scaling_group=name,
                    domain=domain_fixture,
                )
            ) is False

            # After association: True
            binder = RBACScopeBinder(
                pairs=[
                    RBACScopeBindingPair(
                        spec=ScalingGroupForDomainCreatorSpec(
                            scaling_group=name,
                            domain=domain_fixture,
                        ),
                        entity_ref=RBACElementRef(RBACElementType.RESOURCE_GROUP, name),
                        scope_ref=RBACElementRef(RBACElementType.DOMAIN, domain_fixture),
                    )
                ]
            )
            await scaling_group_processors.associate_scaling_group_with_domains.wait_for_complete(
                AssociateScalingGroupWithDomainsAction(binder=binder)
            )
            assert (
                await scaling_group_repository.check_scaling_group_domain_association_exists(
                    scaling_group=name,
                    domain=domain_fixture,
                )
            ) is True
        finally:
            await _purge_sgroup(scaling_group_processors, name)


class TestScalingGroupKeypairAssociation:
    """Keypair association add/remove/check via the processor layer."""

    # ------------------------------------------------------------------
    # S-1: Associate single keypair
    # ------------------------------------------------------------------

    async def test_s1_associate_single_keypair(
        self,
        scaling_group_processors: ScalingGroupProcessors,
        scaling_group_repository: ScalingGroupRepository,
        admin_user_fixture: Any,
        database_fixture: None,
    ) -> None:
        """S-1: Associate a scaling group with a single keypair; association exists in DB."""
        name = f"kp-assoc-{uuid.uuid4().hex[:8]}"
        await _create_sgroup(scaling_group_processors, name)
        access_key = AccessKey(admin_user_fixture.keypair.access_key)
        try:
            bulk_creator = BulkCreator(
                specs=[
                    ScalingGroupForKeypairsCreatorSpec(
                        scaling_group=name,
                        access_key=access_key,
                    )
                ]
            )
            await scaling_group_processors.associate_scaling_group_with_keypairs.wait_for_complete(
                AssociateScalingGroupWithKeypairsAction(bulk_creator=bulk_creator)
            )

            exists = await scaling_group_repository.check_scaling_group_keypair_association_exists(
                scaling_group_name=name,
                access_key=access_key,
            )
            assert exists is True
        finally:
            await _purge_sgroup(scaling_group_processors, name)

    # ------------------------------------------------------------------
    # S-3: Disassociate keypair
    # ------------------------------------------------------------------

    async def test_s3_disassociate_keypair_removes_association(
        self,
        scaling_group_processors: ScalingGroupProcessors,
        scaling_group_repository: ScalingGroupRepository,
        admin_user_fixture: Any,
        database_fixture: None,
    ) -> None:
        """S-3: Disassociate keypair; check_exists returns False afterwards."""
        name = f"kp-disassoc-{uuid.uuid4().hex[:8]}"
        await _create_sgroup(scaling_group_processors, name)
        access_key = AccessKey(admin_user_fixture.keypair.access_key)
        try:
            # First associate
            bulk_creator = BulkCreator(
                specs=[
                    ScalingGroupForKeypairsCreatorSpec(
                        scaling_group=name,
                        access_key=access_key,
                    )
                ]
            )
            await scaling_group_processors.associate_scaling_group_with_keypairs.wait_for_complete(
                AssociateScalingGroupWithKeypairsAction(bulk_creator=bulk_creator)
            )

            # Verify association exists
            assert (
                await scaling_group_repository.check_scaling_group_keypair_association_exists(
                    scaling_group_name=name,
                    access_key=access_key,
                )
            ) is True

            # Now disassociate
            purger = create_scaling_group_for_keypairs_purger(
                scaling_group=name,
                access_key=access_key,
            )
            await (
                scaling_group_processors.disassociate_scaling_group_with_keypairs.wait_for_complete(
                    DisassociateScalingGroupWithKeypairsAction(purger=purger)
                )
            )

            # Association should be gone
            exists = await scaling_group_repository.check_scaling_group_keypair_association_exists(
                scaling_group_name=name,
                access_key=access_key,
            )
            assert exists is False
        finally:
            await _purge_sgroup(scaling_group_processors, name)

    # ------------------------------------------------------------------
    # S-2: Associate multiple keypairs
    # ------------------------------------------------------------------

    async def test_s2_associate_multiple_keypairs(
        self,
        scaling_group_processors: ScalingGroupProcessors,
        scaling_group_repository: ScalingGroupRepository,
        admin_user_fixture: Any,
        regular_user_fixture: Any,
        database_fixture: None,
    ) -> None:
        """S-2: Associate a scaling group with multiple keypairs via BulkCreator."""
        name = f"kp-multi-{uuid.uuid4().hex[:8]}"
        await _create_sgroup(scaling_group_processors, name)
        admin_key = AccessKey(admin_user_fixture.keypair.access_key)
        user_key = AccessKey(regular_user_fixture.keypair.access_key)
        try:
            bulk_creator = BulkCreator(
                specs=[
                    ScalingGroupForKeypairsCreatorSpec(
                        scaling_group=name,
                        access_key=admin_key,
                    ),
                    ScalingGroupForKeypairsCreatorSpec(
                        scaling_group=name,
                        access_key=user_key,
                    ),
                ]
            )
            await scaling_group_processors.associate_scaling_group_with_keypairs.wait_for_complete(
                AssociateScalingGroupWithKeypairsAction(bulk_creator=bulk_creator)
            )

            assert (
                await scaling_group_repository.check_scaling_group_keypair_association_exists(
                    scaling_group_name=name,
                    access_key=admin_key,
                )
            ) is True
            assert (
                await scaling_group_repository.check_scaling_group_keypair_association_exists(
                    scaling_group_name=name,
                    access_key=user_key,
                )
            ) is True
        finally:
            await _purge_sgroup(scaling_group_processors, name)

    # ------------------------------------------------------------------
    # S-5: Check association existence
    # ------------------------------------------------------------------

    async def test_s5_check_keypair_association_existence(
        self,
        scaling_group_processors: ScalingGroupProcessors,
        scaling_group_repository: ScalingGroupRepository,
        admin_user_fixture: Any,
        database_fixture: None,
    ) -> None:
        """S-5: check_scaling_group_keypair_association_exists returns True/False correctly."""
        name = f"kp-check-{uuid.uuid4().hex[:8]}"
        await _create_sgroup(scaling_group_processors, name)
        access_key = AccessKey(admin_user_fixture.keypair.access_key)
        try:
            # Before association: False
            assert (
                await scaling_group_repository.check_scaling_group_keypair_association_exists(
                    scaling_group_name=name,
                    access_key=access_key,
                )
            ) is False

            # After association: True
            bulk_creator = BulkCreator(
                specs=[
                    ScalingGroupForKeypairsCreatorSpec(
                        scaling_group=name,
                        access_key=access_key,
                    )
                ]
            )
            await scaling_group_processors.associate_scaling_group_with_keypairs.wait_for_complete(
                AssociateScalingGroupWithKeypairsAction(bulk_creator=bulk_creator)
            )
            assert (
                await scaling_group_repository.check_scaling_group_keypair_association_exists(
                    scaling_group_name=name,
                    access_key=access_key,
                )
            ) is True
        finally:
            await _purge_sgroup(scaling_group_processors, name)
