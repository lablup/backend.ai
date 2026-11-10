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

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import AccessKey
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.errors.resource import ResourceGroupNotFound
from ai.backend.manager.models.resource_group.creators import (
    ResourceGroupCreator,
    ResourceGroupForDomainRelationCreator,
    ResourceGroupForKeypairRelationCreator,
)
from ai.backend.manager.models.resource_group.purgers import (
    ResourceGroupForDomainRelationPurger,
    ResourceGroupForKeypairRelationPurger,
)
from ai.backend.manager.models.resource_group.updaters import ResourceGroupUpdater
from ai.backend.manager.repositories.rbac.relation_repository import RbacRelationRepository
from ai.backend.manager.repositories.resource_group.repository import ResourceGroupRepository
from ai.backend.manager.services.resource_group.actions.create import CreateResourceGroupAction
from ai.backend.manager.services.resource_group.actions.purge_resource_group import (
    PurgeResourceGroupAction,
)
from ai.backend.manager.services.resource_group.actions.update import UpdateResourceGroupAction
from ai.backend.manager.services.resource_group.service import ResourceGroupService
from ai.backend.manager.types import OptionalState, TriState
from ai.backend.testutils.fixtures import DomainFixtureData

# ---------------------------------------------------------------------------
# Module-level helpers — shared across all test classes
# ---------------------------------------------------------------------------


async def _create_sgroup(
    resource_group_service: ResourceGroupService,
    name: str | None = None,
    *,
    driver: str = "static",
    scheduler: str = "fifo",
    is_public: bool = True,
    is_active: bool = True,
    description: str | None = None,
) -> ResourceGroupData:
    """Create a scaling group."""
    if name is None:
        name = f"test-crud-{uuid.uuid4().hex[:8]}"
    action = CreateResourceGroupAction(
        creator=ResourceGroupCreator(
            name=name,
            driver=driver,
            scheduler=scheduler,
            is_public=is_public,
            is_active=is_active,
            description=description or f"Test scaling group {name}",
        )
    )
    result = await resource_group_service.create_resource_group(action)
    return result.resource_group


async def _purge_sgroup(
    resource_group_service: ResourceGroupService,
    resource_group_id: ResourceGroupID,
) -> None:
    """Purge a scaling group."""
    action = PurgeResourceGroupAction(resource_group_id=resource_group_id)
    await resource_group_service.purge_resource_group(action)


class TestScalingGroupCRUD:
    """Full CRUD lifecycle for scaling groups via the processor layer + real DB."""

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    async def test_s_create_1_basic_create_returns_correct_name(
        self,
        resource_group_service: ResourceGroupService,
        database_fixture: None,
    ) -> None:
        """S-CREATE-1: superadmin creates a scaling group; result has correct name/driver/scheduler."""
        name = f"crud-create-{uuid.uuid4().hex[:8]}"
        sg = await _create_sgroup(
            resource_group_service,
            name,
            driver="static",
            scheduler="fifo",
        )
        try:
            assert isinstance(sg, ResourceGroupData)
            assert sg.name == name
            assert sg.driver.name == "static"
            assert sg.scheduler.name.value == "fifo"
            assert sg.status.is_active is True
            assert sg.status.is_public is True
        finally:
            await _purge_sgroup(resource_group_service, sg.id)

    async def test_s_create_3_private_scaling_group(
        self,
        resource_group_service: ResourceGroupService,
        database_fixture: None,
    ) -> None:
        """S-CREATE-3: private scaling group (is_public=False) is created correctly."""
        name = f"crud-private-{uuid.uuid4().hex[:8]}"
        sg = await _create_sgroup(
            resource_group_service,
            name,
            is_public=False,
        )
        try:
            assert sg.status.is_public is False
        finally:
            await _purge_sgroup(resource_group_service, sg.id)

    # ------------------------------------------------------------------
    # MODIFY
    # ------------------------------------------------------------------

    async def test_s_mod_1_modify_description(
        self,
        resource_group_service: ResourceGroupService,
        database_fixture: None,
    ) -> None:
        """S-MOD-1: Modify description → updated value returned."""
        name = f"crud-mod-{uuid.uuid4().hex[:8]}"
        sg = await _create_sgroup(resource_group_service, name)
        try:
            action = UpdateResourceGroupAction(
                resource_group_id=sg.id,
                updater=ResourceGroupUpdater(
                    resource_group_id=sg.id,
                    description=TriState.update("Updated description"),
                ),
            )
            result = await resource_group_service.update_resource_group(action)
            assert result.resource_group.metadata.description == "Updated description"
        finally:
            await _purge_sgroup(resource_group_service, sg.id)

    async def test_s_mod_2_toggle_public_to_private(
        self,
        resource_group_service: ResourceGroupService,
        database_fixture: None,
    ) -> None:
        """S-MOD-2: Toggle is_public from True to False."""
        name = f"crud-mod2-{uuid.uuid4().hex[:8]}"
        sg = await _create_sgroup(resource_group_service, name, is_public=True)
        assert sg.status.is_public is True
        try:
            action = UpdateResourceGroupAction(
                resource_group_id=sg.id,
                updater=ResourceGroupUpdater(
                    resource_group_id=sg.id,
                    is_public=OptionalState.update(False),
                ),
            )
            result = await resource_group_service.update_resource_group(action)
            assert result.resource_group.status.is_public is False
        finally:
            await _purge_sgroup(resource_group_service, sg.id)

    async def test_s_mod_3_deactivate_scaling_group(
        self,
        resource_group_service: ResourceGroupService,
        database_fixture: None,
    ) -> None:
        """S-MOD-3: Deactivate scaling group (is_active=False)."""
        name = f"crud-mod3-{uuid.uuid4().hex[:8]}"
        sg = await _create_sgroup(resource_group_service, name, is_active=True)
        try:
            action = UpdateResourceGroupAction(
                resource_group_id=sg.id,
                updater=ResourceGroupUpdater(
                    resource_group_id=sg.id,
                    is_active=OptionalState.update(False),
                ),
            )
            result = await resource_group_service.update_resource_group(action)
            assert result.resource_group.status.is_active is False
        finally:
            await _purge_sgroup(resource_group_service, sg.id)

    async def test_s_mod_4_change_driver(
        self,
        resource_group_service: ResourceGroupService,
        database_fixture: None,
    ) -> None:
        """S-MOD-4: Update driver config."""
        name = f"crud-mod4-{uuid.uuid4().hex[:8]}"
        sg = await _create_sgroup(resource_group_service, name, driver="static")
        try:
            action = UpdateResourceGroupAction(
                resource_group_id=sg.id,
                updater=ResourceGroupUpdater(
                    resource_group_id=sg.id,
                    driver=OptionalState.update("static"),
                    driver_opts=OptionalState.update({"key": "value"}),
                ),
            )
            result = await resource_group_service.update_resource_group(action)
            assert result.resource_group.driver.name == "static"
        finally:
            await _purge_sgroup(resource_group_service, sg.id)

    # ------------------------------------------------------------------
    # PURGE
    # ------------------------------------------------------------------

    async def test_s_purge_1_purge_removes_scaling_group(
        self,
        resource_group_service: ResourceGroupService,
        resource_group_repository: ResourceGroupRepository,
        database_fixture: None,
    ) -> None:
        """S-PURGE-1: Purge a scaling group; it is no longer findable."""
        name = f"crud-purge-{uuid.uuid4().hex[:8]}"
        sg = await _create_sgroup(resource_group_service, name)

        action = PurgeResourceGroupAction(resource_group_id=sg.id)
        result = await resource_group_service.purge_resource_group(action)
        assert result.data.name == name

        # Verify it no longer exists
        with pytest.raises(ResourceGroupNotFound):
            await resource_group_repository.get_resource_group_by_name(name)


class TestScalingGroupDomainAssociation:
    """Domain association add/remove/check through the relation operations."""

    # ------------------------------------------------------------------
    # S-1: Associate single domain
    # ------------------------------------------------------------------

    async def test_s1_associate_single_domain(
        self,
        resource_group_service: ResourceGroupService,
        resource_group_repository: ResourceGroupRepository,
        rbac_relation_repository: RbacRelationRepository,
        domain_fixture: DomainFixtureData,
        database_fixture: None,
    ) -> None:
        """S-1: Link a scaling group to a single domain; the association exists in DB."""
        name = f"assoc-dom-{uuid.uuid4().hex[:8]}"
        sg = await _create_sgroup(resource_group_service, name)
        try:
            await rbac_relation_repository.create(
                [(domain_fixture.domain_id, sg.id)], ResourceGroupForDomainRelationCreator()
            )

            exists = await resource_group_repository.check_resource_group_domain_association_exists(
                resource_group_id=sg.id,
                domain_id=domain_fixture.domain_id,
            )
            assert exists is True
        finally:
            await _purge_sgroup(resource_group_service, sg.id)

    # ------------------------------------------------------------------
    # S-3: Disassociate domain
    # ------------------------------------------------------------------

    async def test_s3_disassociate_domain_removes_association(
        self,
        resource_group_service: ResourceGroupService,
        resource_group_repository: ResourceGroupRepository,
        rbac_relation_repository: RbacRelationRepository,
        domain_fixture: DomainFixtureData,
        database_fixture: None,
    ) -> None:
        """S-3: Unlink the domain; check_exists returns False afterwards."""
        name = f"disassoc-dom-{uuid.uuid4().hex[:8]}"
        sg = await _create_sgroup(resource_group_service, name)
        try:
            await rbac_relation_repository.create(
                [(domain_fixture.domain_id, sg.id)], ResourceGroupForDomainRelationCreator()
            )
            assert (
                await resource_group_repository.check_resource_group_domain_association_exists(
                    resource_group_id=sg.id,
                    domain_id=domain_fixture.domain_id,
                )
            ) is True

            unlinked = await rbac_relation_repository.purge(
                [(domain_fixture.domain_id, sg.id)], ResourceGroupForDomainRelationPurger()
            )
            assert unlinked == [True]

            exists = await resource_group_repository.check_resource_group_domain_association_exists(
                resource_group_id=sg.id,
                domain_id=domain_fixture.domain_id,
            )
            assert exists is False
        finally:
            await _purge_sgroup(resource_group_service, sg.id)

    # ------------------------------------------------------------------
    # S-5: Check association existence
    # ------------------------------------------------------------------

    async def test_s5_check_association_existence(
        self,
        resource_group_service: ResourceGroupService,
        resource_group_repository: ResourceGroupRepository,
        rbac_relation_repository: RbacRelationRepository,
        domain_fixture: DomainFixtureData,
        database_fixture: None,
    ) -> None:
        """S-5: check_resource_group_domain_association_exists answers True and False."""
        name = f"check-assoc-{uuid.uuid4().hex[:8]}"
        sg = await _create_sgroup(resource_group_service, name)
        try:
            assert (
                await resource_group_repository.check_resource_group_domain_association_exists(
                    resource_group_id=sg.id,
                    domain_id=domain_fixture.domain_id,
                )
            ) is False

            await rbac_relation_repository.create(
                [(domain_fixture.domain_id, sg.id)], ResourceGroupForDomainRelationCreator()
            )
            assert (
                await resource_group_repository.check_resource_group_domain_association_exists(
                    resource_group_id=sg.id,
                    domain_id=domain_fixture.domain_id,
                )
            ) is True
        finally:
            await _purge_sgroup(resource_group_service, sg.id)

    async def test_unlinking_an_unlinked_pair_is_silent(
        self,
        resource_group_service: ResourceGroupService,
        rbac_relation_repository: RbacRelationRepository,
        domain_fixture: DomainFixtureData,
        database_fixture: None,
    ) -> None:
        """Unlinking a pair that was never linked answers False and raises nothing."""
        name = f"unlinked-dom-{uuid.uuid4().hex[:8]}"
        sg = await _create_sgroup(resource_group_service, name)
        try:
            unlinked = await rbac_relation_repository.purge(
                [(domain_fixture.domain_id, sg.id)], ResourceGroupForDomainRelationPurger()
            )
            assert unlinked == [False]
        finally:
            await _purge_sgroup(resource_group_service, sg.id)


class TestScalingGroupKeypairAssociation:
    """Keypair association add/remove/check through the relation operations.

    The relation names the keypair's owner, not the key: the row keeps the access key
    while the graph edge is per user.
    """

    # ------------------------------------------------------------------
    # S-1: Associate single keypair
    # ------------------------------------------------------------------

    async def test_s1_associate_single_keypair(
        self,
        resource_group_service: ResourceGroupService,
        resource_group_repository: ResourceGroupRepository,
        rbac_relation_repository: RbacRelationRepository,
        admin_user_fixture: Any,
        database_fixture: None,
    ) -> None:
        """S-1: Link a scaling group to a single keypair; the association exists in DB."""
        name = f"kp-assoc-{uuid.uuid4().hex[:8]}"
        sg = await _create_sgroup(resource_group_service, name)
        access_key = AccessKey(admin_user_fixture.keypair.access_key)
        user_id = UserID(admin_user_fixture.user_uuid)
        try:
            await rbac_relation_repository.create(
                [(user_id, sg.id)],
                ResourceGroupForKeypairRelationCreator(access_key=access_key),
            )

            exists = (
                await resource_group_repository.check_resource_group_keypair_association_exists(
                    resource_group_id=sg.id,
                    access_key=access_key,
                )
            )
            assert exists is True
        finally:
            await _purge_sgroup(resource_group_service, sg.id)

    # ------------------------------------------------------------------
    # S-3: Disassociate keypair
    # ------------------------------------------------------------------

    async def test_s3_disassociate_keypair_removes_association(
        self,
        resource_group_service: ResourceGroupService,
        resource_group_repository: ResourceGroupRepository,
        rbac_relation_repository: RbacRelationRepository,
        admin_user_fixture: Any,
        database_fixture: None,
    ) -> None:
        """S-3: Unlink the keypair; check_exists returns False afterwards."""
        name = f"kp-disassoc-{uuid.uuid4().hex[:8]}"
        sg = await _create_sgroup(resource_group_service, name)
        access_key = AccessKey(admin_user_fixture.keypair.access_key)
        user_id = UserID(admin_user_fixture.user_uuid)
        try:
            await rbac_relation_repository.create(
                [(user_id, sg.id)],
                ResourceGroupForKeypairRelationCreator(access_key=access_key),
            )
            assert (
                await resource_group_repository.check_resource_group_keypair_association_exists(
                    resource_group_id=sg.id,
                    access_key=access_key,
                )
            ) is True

            unlinked = await rbac_relation_repository.purge(
                [(user_id, sg.id)], ResourceGroupForKeypairRelationPurger()
            )
            assert unlinked == [True]

            exists = (
                await resource_group_repository.check_resource_group_keypair_association_exists(
                    resource_group_id=sg.id,
                    access_key=access_key,
                )
            )
            assert exists is False
        finally:
            await _purge_sgroup(resource_group_service, sg.id)

    # ------------------------------------------------------------------
    # S-2: Associate keypairs of two owners
    # ------------------------------------------------------------------

    async def test_s2_associate_multiple_keypairs(
        self,
        resource_group_service: ResourceGroupService,
        resource_group_repository: ResourceGroupRepository,
        rbac_relation_repository: RbacRelationRepository,
        admin_user_fixture: Any,
        regular_user_fixture: Any,
        database_fixture: None,
    ) -> None:
        """S-2: Link a scaling group to the keypairs of two owners."""
        name = f"kp-multi-{uuid.uuid4().hex[:8]}"
        sg = await _create_sgroup(resource_group_service, name)
        admin_key = AccessKey(admin_user_fixture.keypair.access_key)
        user_key = AccessKey(regular_user_fixture.keypair.access_key)
        try:
            await rbac_relation_repository.create(
                [(UserID(admin_user_fixture.user_uuid), sg.id)],
                ResourceGroupForKeypairRelationCreator(access_key=admin_key),
            )
            await rbac_relation_repository.create(
                [(UserID(regular_user_fixture.user_uuid), sg.id)],
                ResourceGroupForKeypairRelationCreator(access_key=user_key),
            )

            assert (
                await resource_group_repository.check_resource_group_keypair_association_exists(
                    resource_group_id=sg.id,
                    access_key=admin_key,
                )
            ) is True
            assert (
                await resource_group_repository.check_resource_group_keypair_association_exists(
                    resource_group_id=sg.id,
                    access_key=user_key,
                )
            ) is True
        finally:
            await _purge_sgroup(resource_group_service, sg.id)

    # ------------------------------------------------------------------
    # S-5: Check association existence
    # ------------------------------------------------------------------

    async def test_s5_check_keypair_association_existence(
        self,
        resource_group_service: ResourceGroupService,
        resource_group_repository: ResourceGroupRepository,
        rbac_relation_repository: RbacRelationRepository,
        admin_user_fixture: Any,
        database_fixture: None,
    ) -> None:
        """S-5: check_resource_group_keypair_association_exists answers True and False."""
        name = f"kp-check-{uuid.uuid4().hex[:8]}"
        sg = await _create_sgroup(resource_group_service, name)
        access_key = AccessKey(admin_user_fixture.keypair.access_key)
        user_id = UserID(admin_user_fixture.user_uuid)
        try:
            assert (
                await resource_group_repository.check_resource_group_keypair_association_exists(
                    resource_group_id=sg.id,
                    access_key=access_key,
                )
            ) is False

            await rbac_relation_repository.create(
                [(user_id, sg.id)],
                ResourceGroupForKeypairRelationCreator(access_key=access_key),
            )
            assert (
                await resource_group_repository.check_resource_group_keypair_association_exists(
                    resource_group_id=sg.id,
                    access_key=access_key,
                )
            ) is True
        finally:
            await _purge_sgroup(resource_group_service, sg.id)
