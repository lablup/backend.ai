"""
Tests for TemplateRepository functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.types import DefaultForUnspecified, ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import AssocGroupUserRow, GroupRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.session_template import TemplateType, session_templates
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.template.repository import TemplateRepository
from ai.backend.testutils.db import with_tables


class TestTemplateRepository:
    """Test cases for TemplateRepository CRUD operations."""

    # =========================================================================
    # Fixtures
    # =========================================================================

    @pytest.fixture
    def test_password_info(self) -> PasswordInfo:
        return PasswordInfo(
            password="test_password",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=100_000,
            salt_size=32,
        )

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ScalingGroupRow,
                AgentRow,
                UserResourcePolicyRow,
                KeyPairResourcePolicyRow,
                ProjectResourcePolicyRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                AssocGroupUserRow,
                SessionRow,
                KernelRow,
                session_templates,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            domain = DomainRow(
                name=domain_name,
                description="Test domain",
                is_active=True,
                total_resource_slots=ResourceSlot.from_user_input({"cpu": "4", "mem": "8g"}, None),
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
                allowed_docker_registries=[],
                dotfiles=b"",
                integration_id=None,
            )
            session.add(domain)
            await session.commit()
        return domain_name

    @pytest.fixture
    async def default_user_resource_policy(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        policy_name = "default"
        async with db_with_cleanup.begin_session() as session:
            policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
            session.add(policy)
            await session.commit()
        return policy_name

    @pytest.fixture
    async def default_keypair_resource_policy(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        policy_name = "default"
        async with db_with_cleanup.begin_session() as session:
            policy = KeyPairResourcePolicyRow(
                name=policy_name,
                default_for_unspecified=DefaultForUnspecified.UNLIMITED,
                total_resource_slots=ResourceSlot(),
                max_session_lifetime=0,
                max_concurrent_sessions=30,
                max_concurrent_sftp_sessions=5,
                max_containers_per_session=1,
                idle_timeout=1800,
            )
            session.add(policy)
            await session.commit()
        return policy_name

    @pytest.fixture
    async def test_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: str,
        default_user_resource_policy: str,
        test_password_info: PasswordInfo,
    ) -> uuid.UUID:
        user_uuid = uuid.uuid4()
        async with db_with_cleanup.begin_session() as session:
            user = UserRow(
                uuid=user_uuid,
                username=f"testuser-{user_uuid.hex[:8]}",
                email=f"test-{user_uuid.hex[:8]}@example.com",
                password=test_password_info,
                need_password_change=False,
                full_name="Test User",
                description="Test user",
                status=UserStatus.ACTIVE,
                status_info="active",
                domain_name=test_domain,
                role=UserRole.USER,
                resource_policy=default_user_resource_policy,
            )
            session.add(user)
            await session.commit()
        return user_uuid

    @pytest.fixture
    async def test_superadmin(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: str,
        default_user_resource_policy: str,
        test_password_info: PasswordInfo,
    ) -> uuid.UUID:
        user_uuid = uuid.uuid4()
        async with db_with_cleanup.begin_session() as session:
            user = UserRow(
                uuid=user_uuid,
                username=f"admin-{user_uuid.hex[:8]}",
                email=f"admin-{user_uuid.hex[:8]}@example.com",
                password=test_password_info,
                need_password_change=False,
                full_name="Super Admin",
                description="Superadmin user",
                status=UserStatus.ACTIVE,
                status_info="active",
                domain_name=test_domain,
                role=UserRole.SUPERADMIN,
                resource_policy=default_user_resource_policy,
            )
            session.add(user)
            await session.commit()
        return user_uuid

    @pytest.fixture
    async def test_keypair(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user: uuid.UUID,
        default_keypair_resource_policy: str,
    ) -> str:
        access_key = f"AKIATEST{uuid.uuid4().hex[:12].upper()}"
        async with db_with_cleanup.begin_session() as session:
            keypair = KeyPairRow(
                user_id="testuser",
                access_key=access_key,
                secret_key="testsecretkey1234567890",
                is_active=True,
                is_admin=False,
                user=test_user,
                resource_policy=default_keypair_resource_policy,
            )
            session.add(keypair)
            await session.commit()
        return access_key

    @pytest.fixture
    async def test_project_resource_policy(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        policy_name = "default-project-policy"
        async with db_with_cleanup.begin_session() as session:
            policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=100,
                max_quota_scope_size=-1,
                max_network_count=10,
            )
            session.add(policy)
            await session.commit()
        return policy_name

    @pytest.fixture
    async def test_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: str,
        test_project_resource_policy: str,
    ) -> tuple[uuid.UUID, str]:
        group_id = uuid.uuid4()
        group_name = f"test-group-{group_id.hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            group = GroupRow(
                id=group_id,
                name=group_name,
                description="Test group",
                is_active=True,
                domain_name=test_domain,
                total_resource_slots=ResourceSlot.from_user_input({"cpu": "4", "mem": "8g"}, None),
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
                resource_policy=test_project_resource_policy,
            )
            session.add(group)
            await session.commit()
        return group_id, group_name

    @pytest.fixture
    async def test_user_in_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user: uuid.UUID,
        test_group: tuple[uuid.UUID, str],
    ) -> None:
        group_id, _ = test_group
        async with db_with_cleanup.begin_session() as session:
            assoc = AssocGroupUserRow(
                user_id=test_user,
                group_id=group_id,
            )
            session.add(assoc)
            await session.commit()

    @pytest.fixture
    def template_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> TemplateRepository:
        return TemplateRepository(db=db_with_cleanup)

    # =========================================================================
    # Task Template CRUD Tests
    # =========================================================================

    async def test_create_task_templates_single(
        self,
        template_repository: TemplateRepository,
        test_domain: str,
        test_user: uuid.UUID,
        test_group: tuple[uuid.UUID, str],
    ) -> None:
        group_id, _ = test_group
        template_id = uuid.uuid4().hex
        items = [
            {
                "id": template_id,
                "user_uuid": test_user,
                "group_id": group_id,
                "name": "test-task-template",
                "template": {"apiVersion": "v1", "kind": "taskTemplate"},
            }
        ]

        results = await template_repository.create_task_templates(test_domain, items)

        assert len(results) == 1
        assert results[0]["id"] == template_id
        assert results[0]["user"] == str(test_user)

    async def test_create_task_templates_batch(
        self,
        template_repository: TemplateRepository,
        test_domain: str,
        test_user: uuid.UUID,
        test_group: tuple[uuid.UUID, str],
    ) -> None:
        group_id, _ = test_group
        items = [
            {
                "id": uuid.uuid4().hex,
                "user_uuid": test_user,
                "group_id": group_id,
                "name": f"task-template-{i}",
                "template": {"apiVersion": "v1", "kind": "taskTemplate"},
            }
            for i in range(3)
        ]

        results = await template_repository.create_task_templates(test_domain, items)

        assert len(results) == 3
        for result in results:
            assert result["user"] == str(test_user)

    async def test_get_task_template_exists(
        self,
        template_repository: TemplateRepository,
        test_domain: str,
        test_user: uuid.UUID,
        test_group: tuple[uuid.UUID, str],
    ) -> None:
        group_id, _ = test_group
        template_id = uuid.uuid4().hex
        template_data = {"apiVersion": "v1", "kind": "taskTemplate", "spec": {"image": "python"}}
        items = [
            {
                "id": template_id,
                "user_uuid": test_user,
                "group_id": group_id,
                "name": "my-template",
                "template": template_data,
            }
        ]
        await template_repository.create_task_templates(test_domain, items)

        result = await template_repository.get_task_template(template_id)

        assert result is not None
        assert result["name"] == "my-template"
        assert result["user_uuid"] == test_user
        assert result["group_id"] == group_id
        assert result["template"] == template_data

    async def test_get_task_template_not_found(
        self,
        template_repository: TemplateRepository,
    ) -> None:
        result = await template_repository.get_task_template(uuid.uuid4().hex)
        assert result is None

    async def test_task_template_exists_true(
        self,
        template_repository: TemplateRepository,
        test_domain: str,
        test_user: uuid.UUID,
        test_group: tuple[uuid.UUID, str],
    ) -> None:
        group_id, _ = test_group
        template_id = uuid.uuid4().hex
        items = [
            {
                "id": template_id,
                "user_uuid": test_user,
                "group_id": group_id,
                "name": "exists-check",
                "template": {"apiVersion": "v1"},
            }
        ]
        await template_repository.create_task_templates(test_domain, items)

        assert await template_repository.task_template_exists(template_id) is True

    async def test_task_template_exists_false(
        self,
        template_repository: TemplateRepository,
    ) -> None:
        assert await template_repository.task_template_exists(uuid.uuid4().hex) is False

    async def test_list_task_templates(
        self,
        template_repository: TemplateRepository,
        test_domain: str,
        test_user: uuid.UUID,
        test_group: tuple[uuid.UUID, str],
    ) -> None:
        group_id, group_name = test_group
        items = [
            {
                "id": uuid.uuid4().hex,
                "user_uuid": test_user,
                "group_id": group_id,
                "name": f"list-task-{i}",
                "template": {"apiVersion": "v1", "kind": "taskTemplate"},
            }
            for i in range(2)
        ]
        await template_repository.create_task_templates(test_domain, items)

        entries = await template_repository.list_task_templates(test_user)

        assert len(entries) == 2
        for entry in entries:
            assert entry["is_owner"] is True
            assert entry["user"] == str(test_user)
            assert entry["group"] == str(group_id)
            assert entry["group_name"] == group_name

    async def test_list_task_templates_empty(
        self,
        template_repository: TemplateRepository,
    ) -> None:
        entries = await template_repository.list_task_templates(uuid.uuid4())
        assert entries == []

    async def test_list_task_templates_only_active(
        self,
        template_repository: TemplateRepository,
        test_domain: str,
        test_user: uuid.UUID,
        test_group: tuple[uuid.UUID, str],
    ) -> None:
        group_id, _ = test_group
        active_id = uuid.uuid4().hex
        deleted_id = uuid.uuid4().hex
        items = [
            {
                "id": active_id,
                "user_uuid": test_user,
                "group_id": group_id,
                "name": "active-template",
                "template": {"apiVersion": "v1", "kind": "taskTemplate"},
            },
            {
                "id": deleted_id,
                "user_uuid": test_user,
                "group_id": group_id,
                "name": "deleted-template",
                "template": {"apiVersion": "v1", "kind": "taskTemplate"},
            },
        ]
        await template_repository.create_task_templates(test_domain, items)
        await template_repository.soft_delete_template(deleted_id, TemplateType.TASK)

        entries = await template_repository.list_task_templates(test_user)

        assert len(entries) == 1
        assert entries[0]["id"].hex == active_id

    async def test_update_task_template(
        self,
        template_repository: TemplateRepository,
        test_domain: str,
        test_user: uuid.UUID,
        test_group: tuple[uuid.UUID, str],
    ) -> None:
        group_id, _ = test_group
        template_id = uuid.uuid4().hex
        items = [
            {
                "id": template_id,
                "user_uuid": test_user,
                "group_id": group_id,
                "name": "original",
                "template": {"apiVersion": "v1"},
            }
        ]
        await template_repository.create_task_templates(test_domain, items)

        new_template = {"apiVersion": "v2", "updated": True}
        rowcount = await template_repository.update_task_template(
            template_id, group_id, test_user, "updated-name", new_template
        )

        assert rowcount == 1
        result = await template_repository.get_task_template(template_id)
        assert result is not None
        assert result["name"] == "updated-name"
        assert result["template"] == new_template

    async def test_update_task_template_nonexistent(
        self,
        template_repository: TemplateRepository,
        test_user: uuid.UUID,
        test_group: tuple[uuid.UUID, str],
    ) -> None:
        group_id, _ = test_group
        rowcount = await template_repository.update_task_template(
            uuid.uuid4().hex, group_id, test_user, "name", {"data": True}
        )
        assert rowcount == 0

    # =========================================================================
    # Soft Delete Tests
    # =========================================================================

    async def test_soft_delete_task_template(
        self,
        template_repository: TemplateRepository,
        test_domain: str,
        test_user: uuid.UUID,
        test_group: tuple[uuid.UUID, str],
    ) -> None:
        group_id, _ = test_group
        template_id = uuid.uuid4().hex
        items = [
            {
                "id": template_id,
                "user_uuid": test_user,
                "group_id": group_id,
                "name": "to-delete",
                "template": {"apiVersion": "v1"},
            }
        ]
        await template_repository.create_task_templates(test_domain, items)

        rowcount = await template_repository.soft_delete_template(template_id, TemplateType.TASK)

        assert rowcount == 1
        assert await template_repository.task_template_exists(template_id) is False

    async def test_soft_delete_nonexistent(
        self,
        template_repository: TemplateRepository,
    ) -> None:
        rowcount = await template_repository.soft_delete_template(
            uuid.uuid4().hex, TemplateType.TASK
        )
        assert rowcount == 0

    # =========================================================================
    # Cluster Template CRUD Tests
    # =========================================================================

    async def test_create_cluster_template(
        self,
        template_repository: TemplateRepository,
        test_domain: str,
        test_user: uuid.UUID,
        test_group: tuple[uuid.UUID, str],
    ) -> None:
        group_id, _ = test_group
        template_data = {"apiVersion": "v1", "kind": "clusterTemplate", "spec": {"nodes": []}}

        template_id = await template_repository.create_cluster_template(
            test_domain, group_id, test_user, "cluster-1", template_data
        )

        assert isinstance(template_id, str)
        assert len(template_id) == 32  # hex UUID

    async def test_get_cluster_template_exists(
        self,
        template_repository: TemplateRepository,
        test_domain: str,
        test_user: uuid.UUID,
        test_group: tuple[uuid.UUID, str],
    ) -> None:
        group_id, _ = test_group
        template_data = {"apiVersion": "v1", "kind": "clusterTemplate", "nodes": ["master"]}
        template_id = await template_repository.create_cluster_template(
            test_domain, group_id, test_user, "cluster-get", template_data
        )

        result = await template_repository.get_cluster_template(template_id)

        assert result is not None
        assert result == template_data

    async def test_get_cluster_template_not_found(
        self,
        template_repository: TemplateRepository,
    ) -> None:
        result = await template_repository.get_cluster_template(uuid.uuid4().hex)
        assert result is None

    async def test_cluster_template_exists_true(
        self,
        template_repository: TemplateRepository,
        test_domain: str,
        test_user: uuid.UUID,
        test_group: tuple[uuid.UUID, str],
    ) -> None:
        group_id, _ = test_group
        template_id = await template_repository.create_cluster_template(
            test_domain, group_id, test_user, "exists-check", {"data": True}
        )

        assert await template_repository.cluster_template_exists(template_id) is True

    async def test_cluster_template_exists_false(
        self,
        template_repository: TemplateRepository,
    ) -> None:
        assert await template_repository.cluster_template_exists(uuid.uuid4().hex) is False

    async def test_list_cluster_templates_all(
        self,
        template_repository: TemplateRepository,
        test_domain: str,
        test_user: uuid.UUID,
        test_group: tuple[uuid.UUID, str],
    ) -> None:
        group_id, group_name = test_group
        for i in range(2):
            await template_repository.create_cluster_template(
                test_domain, group_id, test_user, f"cluster-{i}", {"data": i}
            )

        entries = await template_repository.list_cluster_templates_all(test_user)

        assert len(entries) == 2
        for entry in entries:
            assert entry["is_owner"] is True
            assert entry["user"] == str(test_user)
            assert entry["group"] == str(group_id)
            assert entry["group_name"] == group_name

    async def test_list_cluster_templates_all_empty(
        self,
        template_repository: TemplateRepository,
    ) -> None:
        entries = await template_repository.list_cluster_templates_all(uuid.uuid4())
        assert entries == []

    async def test_update_cluster_template(
        self,
        template_repository: TemplateRepository,
        test_domain: str,
        test_user: uuid.UUID,
        test_group: tuple[uuid.UUID, str],
    ) -> None:
        group_id, _ = test_group
        template_id = await template_repository.create_cluster_template(
            test_domain, group_id, test_user, "original", {"v": 1}
        )

        new_data = {"v": 2, "updated": True}
        rowcount = await template_repository.update_cluster_template(
            template_id, new_data, "updated-cluster"
        )

        assert rowcount == 1
        result = await template_repository.get_cluster_template(template_id)
        assert result == new_data

    async def test_update_cluster_template_nonexistent(
        self,
        template_repository: TemplateRepository,
    ) -> None:
        rowcount = await template_repository.update_cluster_template(
            uuid.uuid4().hex, {"v": 1}, "name"
        )
        assert rowcount == 0

    async def test_soft_delete_cluster_template(
        self,
        template_repository: TemplateRepository,
        test_domain: str,
        test_user: uuid.UUID,
        test_group: tuple[uuid.UUID, str],
    ) -> None:
        group_id, _ = test_group
        template_id = await template_repository.create_cluster_template(
            test_domain, group_id, test_user, "to-delete", {"data": True}
        )

        rowcount = await template_repository.soft_delete_template(template_id, TemplateType.CLUSTER)

        assert rowcount == 1
        assert await template_repository.cluster_template_exists(template_id) is False

    # =========================================================================
    # list_accessible_cluster_templates Tests
    # =========================================================================

    async def test_list_accessible_user_templates(
        self,
        template_repository: TemplateRepository,
        test_domain: str,
        test_user: uuid.UUID,
        test_group: tuple[uuid.UUID, str],
    ) -> None:
        """User-type templates are owned by the user."""
        group_id, _ = test_group
        await template_repository.create_cluster_template(
            test_domain, group_id, test_user, "my-cluster", {"data": True}
        )

        entries = await template_repository.list_accessible_cluster_templates(
            test_user, UserRole.USER, test_domain, ["user"]
        )

        assert len(entries) == 1
        assert entries[0]["is_owner"] is True
        assert entries[0]["name"] == "my-cluster"

    async def test_list_accessible_group_templates(
        self,
        template_repository: TemplateRepository,
        test_domain: str,
        test_user: uuid.UUID,
        test_superadmin: uuid.UUID,
        test_group: tuple[uuid.UUID, str],
        test_user_in_group: None,
    ) -> None:
        """Group-type templates from groups the user belongs to (excluding own)."""
        group_id, group_name = test_group
        # Create a template owned by superadmin, visible via group
        await template_repository.create_cluster_template(
            test_domain, group_id, test_superadmin, "admin-cluster", {"data": True}
        )

        entries = await template_repository.list_accessible_cluster_templates(
            test_user, UserRole.USER, test_domain, ["user", "group"]
        )

        group_entries = [e for e in entries if e["group_name"] == group_name]
        assert len(group_entries) == 1
        assert group_entries[0]["is_owner"] is False

    async def test_list_accessible_with_group_id_filter(
        self,
        template_repository: TemplateRepository,
        test_domain: str,
        test_user: uuid.UUID,
        test_group: tuple[uuid.UUID, str],
    ) -> None:
        group_id, _ = test_group
        await template_repository.create_cluster_template(
            test_domain, group_id, test_user, "filtered", {"data": True}
        )

        # Filter by the correct group
        entries = await template_repository.list_accessible_cluster_templates(
            test_user, UserRole.USER, test_domain, ["user"], group_id_filter=group_id
        )
        assert len(entries) == 1

        # Filter by a different group
        entries = await template_repository.list_accessible_cluster_templates(
            test_user, UserRole.USER, test_domain, ["user"], group_id_filter=uuid.uuid4()
        )
        assert len(entries) == 0

    # =========================================================================
    # resolve_owner Tests
    # =========================================================================

    async def test_resolve_owner_self(
        self,
        template_repository: TemplateRepository,
        test_domain: str,
        test_user: uuid.UUID,
        test_keypair: str,
        test_group: tuple[uuid.UUID, str],
        test_user_in_group: None,
    ) -> None:
        """When no owner_access_key override, resolves to the requester."""
        _, group_name = test_group
        owner_uuid, group_id = await template_repository.resolve_owner(
            requester_uuid=test_user,
            requester_access_key=test_keypair,
            requester_role=UserRole.USER,
            requester_domain=test_domain,
            requesting_domain=test_domain,
            requesting_group=group_name,
        )

        assert owner_uuid == test_user
        assert isinstance(group_id, uuid.UUID)

    async def test_resolve_owner_invalid_domain(
        self,
        template_repository: TemplateRepository,
        test_domain: str,
        test_user: uuid.UUID,
        test_keypair: str,
        test_group: tuple[uuid.UUID, str],
        test_user_in_group: None,
    ) -> None:
        """Regular user cannot set domain different from their own."""
        _, group_name = test_group
        with pytest.raises(InvalidAPIParameters, match="domain"):
            await template_repository.resolve_owner(
                requester_uuid=test_user,
                requester_access_key=test_keypair,
                requester_role=UserRole.USER,
                requester_domain=test_domain,
                requesting_domain="other-domain",
                requesting_group=group_name,
            )

    async def test_resolve_owner_invalid_group(
        self,
        template_repository: TemplateRepository,
        test_domain: str,
        test_user: uuid.UUID,
        test_keypair: str,
    ) -> None:
        """Non-existent group raises InvalidAPIParameters."""
        with pytest.raises(InvalidAPIParameters, match="group"):
            await template_repository.resolve_owner(
                requester_uuid=test_user,
                requester_access_key=test_keypair,
                requester_role=UserRole.USER,
                requester_domain=test_domain,
                requesting_domain=test_domain,
                requesting_group="nonexistent-group",
            )
