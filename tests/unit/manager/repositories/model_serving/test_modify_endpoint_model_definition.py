"""
Regression test: when model-definition.yaml is updated on disk and
modify_endpoint is called, the new revision must contain the fresh
model_definition — not the previous revision's stale snapshot.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import sqlalchemy as sa

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.user.types import UserData
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.image.types import ImageType
from ai.backend.manager.data.model_serving.types import EndpointLifecycle
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_slot.row import (
    DeploymentRevisionResourceSlotRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.routing.row import RoutingRow
from ai.backend.manager.models.scaling_group.row import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.base import Updater
from ai.backend.manager.repositories.model_serving.repository import ModelServingRepository
from ai.backend.manager.repositories.model_serving.updaters import EndpointUpdaterSpec
from ai.backend.manager.services.model_serving.actions.modify_endpoint import ModifyEndpointAction
from ai.backend.manager.types import TriState
from ai.backend.testutils.db import with_tables

OLD_MODEL_DEF = {"models": [{"name": "old-snapshot"}]}
NEW_MODEL_DEF = {"models": [{"name": "updated-from-disk"}]}


class TestModifyEndpointModelDefinitionRefresh:
    """Verify that modify_endpoint re-reads model_definition from vfolder."""

    # =========================================================================
    # Fixtures
    # =========================================================================

    @pytest.fixture()
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                ContainerRegistryRow,
                ImageRow,
                VFolderRow,
                SessionRow,
                EndpointRow,
                RoutingRow,
                DeploymentRevisionRow,
                ResourceSlotTypeRow,
                DeploymentRevisionResourceSlotRow,
            ],
        ):
            yield database_connection

    @pytest.fixture()
    async def test_domain(self, db_with_cleanup: ExtendedAsyncSAEngine) -> str:
        name = f"test-domain-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as sess:
            sess.add(DomainRow(name=name, total_resource_slots=ResourceSlot()))
            await sess.flush()
        return name

    @pytest.fixture()
    async def test_scaling_group(self, db_with_cleanup: ExtendedAsyncSAEngine) -> str:
        name = f"test-sg-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                ScalingGroupRow(
                    name=name, driver="static", scheduler="fifo", scheduler_opts=ScalingGroupOpts()
                )
            )
            await sess.flush()
        return name

    @pytest.fixture()
    async def test_user_id(
        self, db_with_cleanup: ExtendedAsyncSAEngine, test_domain: str
    ) -> uuid.UUID:
        user_id = uuid.uuid4()
        email = f"test-{uuid.uuid4().hex[:8]}@test.com"
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                UserResourcePolicyRow(
                    name="default",
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            await sess.flush()
            # Create user without main_access_key first (FK to keypairs)
            sess.add(
                UserRow(
                    uuid=user_id,
                    email=email,
                    username=f"testuser-{uuid.uuid4().hex[:8]}",
                    password=PasswordInfo(
                        password="pw",
                        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                        rounds=1,
                        salt_size=16,
                    ),
                    domain_name=test_domain,
                    resource_policy="default",
                    role=UserRole.SUPERADMIN,
                    status=UserStatus.ACTIVE,
                )
            )
            await sess.flush()
            sess.add(
                KeyPairResourcePolicyRow(
                    name="default",
                    total_resource_slots=ResourceSlot(),
                    max_session_lifetime=0,
                    max_concurrent_sessions=10,
                    max_concurrent_sftp_sessions=1,
                    max_containers_per_session=1,
                    idle_timeout=3600,
                )
            )
            await sess.flush()
            sess.add(
                KeyPairRow(
                    user_id=email,
                    access_key="TESTKEY",
                    secret_key="TESTSECRET",
                    is_active=True,
                    is_admin=True,
                    user=user_id,
                    resource_policy="default",
                )
            )
            await sess.flush()
            # Now set main_access_key after keypair exists
            await sess.execute(
                sa.update(UserRow).where(UserRow.uuid == user_id).values(main_access_key="TESTKEY")
            )
            await sess.flush()
        return user_id

    @pytest.fixture()
    async def test_group_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: str,
    ) -> uuid.UUID:
        group_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                ProjectResourcePolicyRow(
                    name="default",
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_network_count=3,
                )
            )
            await sess.flush()
            sess.add(
                GroupRow(
                    id=group_id,
                    name=f"test-grp-{uuid.uuid4().hex[:8]}",
                    domain_name=test_domain,
                    total_resource_slots=ResourceSlot(),
                    resource_policy="default",
                )
            )
            await sess.flush()
        return group_id

    @pytest.fixture()
    async def test_image_id(self, db_with_cleanup: ExtendedAsyncSAEngine) -> uuid.UUID:
        image_id = uuid.uuid4()
        registry_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                ContainerRegistryRow(
                    id=registry_id,
                    url="http://test.local",
                    registry_name=f"test-reg-{uuid.uuid4().hex[:8]}",
                    type=ContainerRegistryType.DOCKER,
                )
            )
            await sess.flush()
            image = ImageRow(
                name=f"test-img-{uuid.uuid4().hex[:8]}",
                project=None,
                image=f"test-img:{uuid.uuid4().hex[:8]}",
                tag="latest",
                registry=f"test-reg-{uuid.uuid4().hex[:8]}",
                registry_id=registry_id,
                architecture="aarch64",
                config_digest="sha256:" + "a" * 64,
                size_bytes=1024,
                type=ImageType.COMPUTE,
                labels={},
                resources={"cpu": {"min": "1"}, "mem": {"min": "64m"}},
            )
            image.id = image_id
            sess.add(image)
            await sess.flush()
        return image_id

    @pytest.fixture()
    async def endpoint_and_revision(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user_id: uuid.UUID,
        test_domain: str,
        test_group_id: uuid.UUID,
        test_scaling_group: str,
        test_image_id: uuid.UUID,
    ) -> tuple[uuid.UUID, uuid.UUID]:
        """Create endpoint + revision with OLD model_definition. Returns (endpoint_id, revision_id)."""
        endpoint_id = uuid.uuid4()
        revision_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                EndpointRow(
                    id=endpoint_id,
                    name=f"test-ep-{uuid.uuid4().hex[:8]}",
                    created_user=test_user_id,
                    session_owner=test_user_id,
                    domain=test_domain,
                    project=test_group_id,
                    resource_group=test_scaling_group,
                    lifecycle_stage=EndpointLifecycle.READY,
                    replicas=1,
                )
            )
            await sess.flush()

            sess.add(ResourceSlotTypeRow(slot_name="cpu", slot_type="count"))
            sess.add(ResourceSlotTypeRow(slot_name="mem", slot_type="bytes"))
            await sess.flush()

            sess.add(
                DeploymentRevisionRow(
                    id=revision_id,
                    endpoint=endpoint_id,
                    revision_number=1,
                    image=test_image_id,
                    model_mount_destination="/models",
                    model_definition_path="model-definition.yaml",
                    model_definition=OLD_MODEL_DEF,
                    resource_group=test_scaling_group,
                    resource_opts={},
                    cluster_mode="single-node",
                    cluster_size=1,
                    environ={},
                    runtime_variant="custom",
                    extra_mounts=[],
                )
            )
            await sess.flush()

            sess.add(
                DeploymentRevisionResourceSlotRow(
                    revision_id=revision_id,
                    slot_name="cpu",
                    quantity="1",
                )
            )
            sess.add(
                DeploymentRevisionResourceSlotRow(
                    revision_id=revision_id,
                    slot_name="mem",
                    quantity="268435456",
                )
            )
            await sess.flush()

            await sess.execute(
                sa.update(EndpointRow)
                .where(EndpointRow.id == endpoint_id)
                .values(current_revision=revision_id)
            )
            await sess.flush()
        return endpoint_id, revision_id

    @pytest.fixture()
    def repository(self, db_with_cleanup: ExtendedAsyncSAEngine) -> ModelServingRepository:
        return ModelServingRepository(db=db_with_cleanup)

    @pytest.fixture()
    def user_context(self, test_user_id: uuid.UUID) -> UserData:
        return UserData(
            user_id=test_user_id,
            is_authorized=True,
            is_admin=True,
            is_superadmin=True,
            role=UserRole.SUPERADMIN,
            domain_name="default",
        )

    # =========================================================================
    # Tests
    # =========================================================================

    async def test_new_revision_uses_refreshed_model_definition(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        repository: ModelServingRepository,
        endpoint_and_revision: tuple[uuid.UUID, uuid.UUID],
        user_context: UserData,
    ) -> None:
        """The new revision created by modify_endpoint must carry the model
        definition re-read from the vfolder, not the old revision's copy."""

        endpoint_id, _ = endpoint_and_revision
        spec = EndpointUpdaterSpec(environ=TriState.update({"NEW_VAR": "1"}))
        action = ModifyEndpointAction(
            endpoint_id=endpoint_id,
            updater=Updater(spec=spec, pk_value=endpoint_id),
        )

        with (
            with_user(user_context),
            patch.object(
                repository,
                "_fetch_model_definition_from_vfolder",
                new_callable=AsyncMock,
                return_value=NEW_MODEL_DEF,
            ),
            patch(
                "ai.backend.manager.repositories.model_serving.repository.ModelServiceHelper",
                check_scaling_group=AsyncMock(),
            ),
        ):
            result = await repository.modify_endpoint(
                action,
                agent_registry=MagicMock(),
                legacy_etcd_config_loader=MagicMock(),
                storage_manager=MagicMock(),
            )

        assert result.success is True

        # Verify the new revision in DB has the refreshed model_definition
        async with db_with_cleanup.begin_readonly_session() as sess:
            rows = (
                (
                    await sess.execute(
                        sa.select(DeploymentRevisionRow)
                        .where(DeploymentRevisionRow.endpoint == endpoint_id)
                        .order_by(DeploymentRevisionRow.revision_number)
                    )
                )
                .scalars()
                .all()
            )

        assert len(rows) == 2
        assert rows[0].model_definition == OLD_MODEL_DEF
        assert rows[1].model_definition == NEW_MODEL_DEF, (
            "New revision must use model_definition freshly read from vfolder, "
            f"got {rows[1].model_definition!r}"
        )
