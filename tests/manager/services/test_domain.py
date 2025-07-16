from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncGenerator
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa

from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow, ProjectType
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.domain.repositories import (
    DomainRepositories,
    RepositoryArgs,
)
from ai.backend.manager.services.domain.actions.create_domain import (
    CreateDomainAction,
    CreateDomainActionResult,
)
from ai.backend.manager.services.domain.actions.create_domain_node import (
    CreateDomainNodeAction,
    CreateDomainNodeActionResult,
)
from ai.backend.manager.services.domain.actions.delete_domain import (
    DeleteDomainAction,
    DeleteDomainActionResult,
)
from ai.backend.manager.services.domain.actions.modify_domain import (
    ModifyDomainAction,
    ModifyDomainActionResult,
)
from ai.backend.manager.services.domain.actions.modify_domain_node import (
    ModifyDomainNodeAction,
    ModifyDomainNodeActionResult,
)
from ai.backend.manager.services.domain.actions.purge_domain import (
    PurgeDomainAction,
    PurgeDomainActionResult,
)
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.domain.service import DomainService
from ai.backend.manager.services.domain.types import (
    DomainCreator,
    DomainData,
    DomainModifier,
    DomainNodeModifier,
    UserInfo,
)
from ai.backend.manager.types import OptionalState, TriState

from .test_utils import TestScenario


@pytest.fixture
def processors(database_fixture, database_engine) -> DomainProcessors:
    repository_args = RepositoryArgs(
        db=database_engine,
        storage_manager=MagicMock(),  # Not used by DomainRepositories
        config_provider=MagicMock(),  # Not used by DomainRepositories
        valkey_stat_client=MagicMock(),  # Not used by DomainRepositories
    )
    domain_repositories = DomainRepositories.create(repository_args)
    domain_service = DomainService(
        repository=domain_repositories.repository,
        admin_repository=domain_repositories.admin_repository,
    )
    return DomainProcessors(domain_service, [])


@pytest.fixture
def admin_user() -> UserInfo:
    return UserInfo(
        id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
        role=UserRole.ADMIN,
        domain_name="default",
    )


@pytest.fixture
def superadmin_user() -> UserInfo:
    return UserInfo(
        id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
        role=UserRole.SUPERADMIN,
        domain_name="default",
    )


@pytest.fixture
def regular_user() -> UserInfo:
    return UserInfo(
        id=UUID("dfa9da54-4b28-432f-be29-c0d680c7a412"),
        role=UserRole.USER,
        domain_name="default",
    )


@asynccontextmanager
async def create_domain(
    database_engine: ExtendedAsyncSAEngine, name: str = "test-domain"
) -> AsyncGenerator[str, None]:
    domain_name = name
    async with database_engine.begin() as conn:
        domain_data: dict[str, Any] = {
            "name": domain_name,
            "description": f"Test Domain for {name}",
            "is_active": True,
            "total_resource_slots": {},
            "allowed_vfolder_hosts": {},
            "allowed_docker_registries": [],
            "integration_id": None,
        }
        await conn.execute(sa.insert(DomainRow).values(domain_data).returning(DomainRow))

    try:
        yield domain_name
    finally:
        async with database_engine.begin() as conn:
            await conn.execute(sa.delete(DomainRow).where(DomainRow.name == domain_name))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "Create a domain node",
            CreateDomainNodeAction(
                creator=DomainCreator(
                    name="test-create-domain-node",
                    description="Test domain",
                    total_resource_slots=ResourceSlot.from_user_input({}, None),
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                    integration_id=None,
                    dotfiles=b"\x90",
                ),
                user_info=UserInfo(
                    id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                    role=UserRole.ADMIN,
                    domain_name="default",
                ),
                scaling_groups=None,
            ),
            CreateDomainNodeActionResult(
                domain_data=DomainData(
                    name="test-create-domain-node",
                    description="Test domain",
                    is_active=True,
                    created_at=datetime.now(),
                    modified_at=datetime.now(),
                    total_resource_slots=ResourceSlot.from_user_input({}, None),
                    allowed_vfolder_hosts=VFolderHostPermissionMap({}),
                    allowed_docker_registries=[],
                    dotfiles=b"\x90",
                    integration_id=None,
                ),
                success=True,
                description="domain test-create-domain-node created",
            ),
        ),
        TestScenario.failure(
            "Create domain node with duplicated name",
            CreateDomainNodeAction(
                creator=DomainCreator(
                    name="default",
                    description="Test domain",
                ),
                user_info=UserInfo(
                    id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                    role=UserRole.ADMIN,
                    domain_name="default",
                ),
            ),
            ValueError,
        ),
    ],
)
async def test_create_domain_node(
    processors: DomainProcessors,
    test_scenario: TestScenario[CreateDomainNodeAction, CreateDomainNodeActionResult],
) -> None:
    await test_scenario.test(processors.create_domain_node.wait_for_complete)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "Modify a domain node",
            ModifyDomainNodeAction(
                name="test-modify-domain-node",
                user_info=UserInfo(
                    id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                    role=UserRole.SUPERADMIN,
                    domain_name="default",
                ),
                modifier=DomainNodeModifier(
                    description=TriState.update("Domain Description Modified"),
                ),
            ),
            ModifyDomainNodeActionResult(
                domain_data=DomainData(
                    name="test-modify-domain-node",
                    description="Domain Description Modified",
                    is_active=True,
                    created_at=datetime.now(),
                    modified_at=datetime.now(),
                    total_resource_slots=ResourceSlot.from_user_input({}, None),
                    allowed_vfolder_hosts=VFolderHostPermissionMap({}),
                    allowed_docker_registries=[],
                    dotfiles=b"\x90",
                    integration_id=None,
                ),
                success=True,
                description="domain test-modify-domain-node modified",
            ),
        ),
        TestScenario.failure(
            "Modify a domain not exists",
            ModifyDomainNodeAction(
                name="not-exist-domain",
                user_info=UserInfo(
                    id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                    role=UserRole.SUPERADMIN,
                    domain_name="default",
                ),
                modifier=DomainNodeModifier(
                    description=TriState.update("Domain Description Modified"),
                ),
            ),
            ValueError,
        ),
        TestScenario.failure(
            "Modify a domain without enough permission",
            ModifyDomainNodeAction(
                name="not-exist-domain",
                user_info=UserInfo(
                    id=UUID("dfa9da54-4b28-432f-be29-c0d680c7a412"),
                    role=UserRole.USER,
                    domain_name="default",
                ),
                modifier=DomainNodeModifier(
                    description=TriState.update("Domain Description Modified"),
                ),
            ),
            ValueError,
        ),
    ],
)
async def test_modify_domain_node(
    processors: DomainProcessors,
    test_scenario: TestScenario[ModifyDomainNodeAction, ModifyDomainNodeActionResult],
    database_engine,
) -> None:
    async with create_domain(database_engine, "test-modify-domain-node"):
        await test_scenario.test(processors.modify_domain_node.wait_for_complete)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "Create a domain",
            CreateDomainAction(
                creator=DomainCreator(
                    name="test-create-domain",
                    description="Test domain",
                ),
                user_info=UserInfo(
                    id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                    role=UserRole.ADMIN,
                    domain_name="default",
                ),
            ),
            CreateDomainActionResult(
                domain_data=DomainData(
                    name="test-create-domain",
                    description="Test domain",
                    is_active=True,
                    created_at=datetime.now(),
                    modified_at=datetime.now(),
                    total_resource_slots=ResourceSlot.from_user_input({}, None),
                    allowed_vfolder_hosts=VFolderHostPermissionMap({}),
                    allowed_docker_registries=[],
                    dotfiles=b"\x90",
                    integration_id=None,
                ),
                success=True,
                description="domain creation succeed",
            ),
        ),
        TestScenario.success(
            "Create a domain with duplicated name, return none",
            CreateDomainAction(
                creator=DomainCreator(
                    name="default",
                    description="Test domain",
                ),
                user_info=UserInfo(
                    id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                    role=UserRole.ADMIN,
                    domain_name="default",
                ),
            ),
            CreateDomainActionResult(
                domain_data=None,
                success=False,
                description="integrity error",
            ),
        ),
        TestScenario.success(
            "Create a domain with empty name, return failure",
            CreateDomainAction(
                creator=DomainCreator(
                    name="",
                    description="Test domain with empty name",
                ),
                user_info=UserInfo(
                    id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                    role=UserRole.ADMIN,
                    domain_name="default",
                ),
            ),
            CreateDomainActionResult(
                domain_data=None,
                success=False,
                description="domain creation failed",
            ),
        ),
        TestScenario.success(
            "Create a domain with complex resource slots",
            CreateDomainAction(
                creator=DomainCreator(
                    name="test-complex-resources",
                    description="Test domain with complex resource slots",
                    total_resource_slots=ResourceSlot.from_user_input(
                        {"cpu": "10", "memory": "64G", "cuda.device": "2"}, None
                    ),
                    allowed_vfolder_hosts={
                        "host1": ["upload-file", "download-file", "mount-in-session"],
                        "host2": ["download-file", "mount-in-session"],
                    },
                    allowed_docker_registries=["docker.io", "registry.example.com"],
                ),
                user_info=UserInfo(
                    id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                    role=UserRole.ADMIN,
                    domain_name="default",
                ),
            ),
            CreateDomainActionResult(
                domain_data=DomainData(
                    name="test-complex-resources",
                    description="Test domain with complex resource slots",
                    is_active=True,
                    created_at=datetime.now(),
                    modified_at=datetime.now(),
                    total_resource_slots=ResourceSlot.from_user_input(
                        {"cpu": "10", "memory": "64G", "cuda.device": "2"}, None
                    ),
                    allowed_vfolder_hosts=VFolderHostPermissionMap({
                        "host1": {"upload-file", "download-file", "mount-in-session"},
                        "host2": {"download-file", "mount-in-session"},
                    }),
                    allowed_docker_registries=["docker.io", "registry.example.com"],
                    dotfiles=b"\x90",
                    integration_id=None,
                ),
                success=True,
                description="domain creation succeed",
            ),
        ),
    ],
)
async def test_create_domain(
    processors: DomainProcessors,
    test_scenario: TestScenario[CreateDomainAction, CreateDomainActionResult],
) -> None:
    await test_scenario.test(processors.create_domain.wait_for_complete)


@pytest.mark.asyncio
async def test_create_model_store_after_domain_created(
    processors: DomainProcessors, database_engine, admin_user
) -> None:
    domain_name = "test-create-domain-post-func"
    action = CreateDomainAction(creator=DomainCreator(name=domain_name), user_info=admin_user)

    await processors.create_domain.wait_for_complete(action)

    async with database_engine.begin_session() as session:
        domain = await session.scalar(
            sa.select(GroupRow).where(
                (GroupRow.name == "model-store") & (GroupRow.domain_name == domain_name)
            )
        )

        assert domain is not None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "Modify domain",
            ModifyDomainAction(
                domain_name="test-modify-domain",
                user_info=UserInfo(
                    id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                    role=UserRole.ADMIN,
                    domain_name="default",
                ),
                modifier=DomainModifier(
                    description=TriState.update("Domain Description Modified"),
                ),
            ),
            ModifyDomainActionResult(
                domain_data=DomainData(
                    name="test-modify-domain",
                    description="Domain Description Modified",
                    is_active=True,
                    created_at=datetime.now(),
                    modified_at=datetime.now(),
                    total_resource_slots=ResourceSlot.from_user_input({}, None),
                    allowed_vfolder_hosts=VFolderHostPermissionMap({}),
                    allowed_docker_registries=[],
                    dotfiles=b"\x90",
                    integration_id=None,
                ),
                success=True,
                description="domain modification succeed",
            ),
        ),
        TestScenario.success(
            "Modify a domain not exists",
            ModifyDomainAction(
                domain_name="not-exist-domain",
                user_info=UserInfo(
                    id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                    role=UserRole.ADMIN,
                    domain_name="default",
                ),
                modifier=DomainModifier(
                    description=TriState.update("Domain Description Modified"),
                ),
            ),
            ModifyDomainActionResult(
                domain_data=None,
                success=False,
                description="domain not found",
            ),
        ),
        TestScenario.success(
            "Modify domain deactivation",
            ModifyDomainAction(
                domain_name="test-modify-domain-deactivate",
                user_info=UserInfo(
                    id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                    role=UserRole.ADMIN,
                    domain_name="default",
                ),
                modifier=DomainModifier(
                    is_active=OptionalState.update(False),
                ),
            ),
            ModifyDomainActionResult(
                domain_data=DomainData(
                    name="test-modify-domain-deactivate",
                    description="Test Domain for test-modify-domain-deactivate",
                    is_active=False,
                    created_at=datetime.now(),
                    modified_at=datetime.now(),
                    total_resource_slots=ResourceSlot.from_user_input({}, None),
                    allowed_vfolder_hosts=VFolderHostPermissionMap({}),
                    allowed_docker_registries=[],
                    dotfiles=b"\x90",
                    integration_id=None,
                ),
                success=True,
                description="domain modification succeed",
            ),
        ),
        TestScenario.success(
            "Modify domain with nullify fields",
            ModifyDomainAction(
                domain_name="test-modify-domain-nullify",
                user_info=UserInfo(
                    id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                    role=UserRole.ADMIN,
                    domain_name="default",
                ),
                modifier=DomainModifier(
                    description=TriState.nullify(),
                    integration_id=TriState.nullify(),
                ),
            ),
            ModifyDomainActionResult(
                domain_data=DomainData(
                    name="test-modify-domain-nullify",
                    description=None,
                    is_active=True,
                    created_at=datetime.now(),
                    modified_at=datetime.now(),
                    total_resource_slots=ResourceSlot.from_user_input({}, None),
                    allowed_vfolder_hosts=VFolderHostPermissionMap({}),
                    allowed_docker_registries=[],
                    dotfiles=b"\x90",
                    integration_id=None,
                ),
                success=True,
                description="domain modification succeed",
            ),
        ),
    ],
)
async def test_modify_domain(
    processors: DomainProcessors,
    test_scenario: TestScenario[ModifyDomainAction, ModifyDomainActionResult],
    database_engine,
) -> None:
    test_domain_name = test_scenario.input.domain_name
    if test_domain_name != "not-exist-domain":
        async with create_domain(database_engine, test_domain_name):
            await test_scenario.test(processors.modify_domain.wait_for_complete)
    else:
        await test_scenario.test(processors.modify_domain.wait_for_complete)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "Delete a domain",
            DeleteDomainAction(
                name="test-delete-domain",
                user_info=UserInfo(
                    id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                    role=UserRole.ADMIN,
                    domain_name="default",
                ),
            ),
            DeleteDomainActionResult(
                success=True,
                description="domain test-delete-domain deleted successfully",
            ),
        ),
        TestScenario.success(
            "Delete a domain not exists",
            DeleteDomainAction(
                name="not-exist-domain",
                user_info=UserInfo(
                    id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                    role=UserRole.ADMIN,
                    domain_name="default",
                ),
            ),
            DeleteDomainActionResult(
                success=False,
                description="no matching not-exist-domain",
            ),
        ),
    ],
)
async def test_delete_domain(
    processors: DomainProcessors,
    test_scenario: TestScenario[DeleteDomainAction, DeleteDomainActionResult],
    database_engine,
) -> None:
    async with create_domain(database_engine, "test-delete-domain"):
        await test_scenario.test(processors.delete_domain.wait_for_complete)


@pytest.mark.asyncio
async def test_delete_domain_in_db(
    processors: DomainProcessors,
    database_engine,
    admin_user,
) -> None:
    async with create_domain(database_engine, "test-delete-domain-in-db") as domain_name:
        async with database_engine.begin_session() as session:
            domain = await session.scalar(
                sa.select(DomainRow).where(
                    (DomainRow.name == domain_name) & (DomainRow.is_active == True)  # noqa
                )
            )

        await processors.delete_domain.wait_for_complete(
            DeleteDomainAction(name=domain_name, user_info=admin_user)
        )

        async with database_engine.begin_session() as session:
            domain = await session.scalar(
                sa.select(DomainRow).where(
                    (DomainRow.name == domain_name) & (DomainRow.is_active == True)  # noqa
                )
            )

            assert domain is None

            domain = await session.scalar(
                sa.select(DomainRow).where(
                    (DomainRow.name == domain_name) & (DomainRow.is_active == False)  # noqa
                )
            )

            assert domain is not None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "Purge a domain",
            PurgeDomainAction(
                name="test-purge-domain",
                user_info=UserInfo(
                    id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                    role=UserRole.ADMIN,
                    domain_name="default",
                ),
            ),
            PurgeDomainActionResult(
                success=True,
                description="domain test-purge-domain purged successfully",
            ),
        ),
        TestScenario.success(
            "Purge a domain not exists",
            PurgeDomainAction(
                name="not-exist-domain",
                user_info=UserInfo(
                    id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                    role=UserRole.ADMIN,
                    domain_name="default",
                ),
            ),
            PurgeDomainActionResult(
                success=False,
                description="no matching not-exist-domain domain to purge",
            ),
        ),
    ],
)
async def test_purge_domain(
    processors: DomainProcessors,
    test_scenario: TestScenario[PurgeDomainAction, PurgeDomainActionResult],
    database_engine,
) -> None:
    async with create_domain(database_engine, "test-purge-domain"):
        await test_scenario.test(processors.purge_domain.wait_for_complete)


@pytest.mark.asyncio
async def test_purge_domain_in_db(
    processors: DomainProcessors, database_engine, admin_user
) -> None:
    domain_name = "test-purge-domain-in-db"
    # create domain
    async with create_domain(database_engine, domain_name):
        # delete domain(soft delete) and delete model-store group
        await processors.delete_domain.wait_for_complete(
            DeleteDomainAction(name=domain_name, user_info=admin_user)
        )
        async with database_engine.begin_session() as session:
            await session.execute(
                sa.update(GroupRow)
                .where((GroupRow.name == "model-store") & (GroupRow.domain_name == domain_name))
                .values({"is_active": False})
            )

            domain = await session.scalar(sa.select(DomainRow).where(DomainRow.name == domain_name))
            assert domain is not None

        # purge domain
        await processors.purge_domain.wait_for_complete(
            PurgeDomainAction(name=domain_name, user_info=admin_user)
        )
        async with database_engine.begin_session() as session:
            domain = await session.scalar(sa.select(DomainRow).where(DomainRow.name == domain_name))

            assert domain is None


@asynccontextmanager
async def create_test_user(
    database_engine: ExtendedAsyncSAEngine, email: str, domain_name: str
) -> AsyncGenerator[UUID, None]:
    user_id = uuid4()
    async with database_engine.begin() as conn:
        user_data = {
            "uuid": user_id,
            "username": "testuser",
            "email": email,
            "password": "password123",
            "need_password_change": False,
            "full_name": "Test User",
            "description": "Test user for domain tests",
            "status": UserStatus.ACTIVE,
            "domain_name": domain_name,
            "role": UserRole.USER,
            "resource_policy": "default",
            "allowed_client_ip": None,
            "totp_activated": False,
            "sudo_session_enabled": False,
            "main_access_key": None,
            "container_uid": None,
            "container_main_gid": None,
            "container_gids": None,
        }
        await conn.execute(sa.insert(UserRow).values(user_data))

    try:
        yield user_id
    finally:
        async with database_engine.begin() as conn:
            await conn.execute(sa.delete(UserRow).where(UserRow.uuid == user_id))


@asynccontextmanager
async def create_test_group(
    database_engine: ExtendedAsyncSAEngine, name: str, domain_name: str
) -> AsyncGenerator[UUID, None]:
    group_id = uuid4()
    async with database_engine.begin() as conn:
        group_data = {
            "id": group_id,
            "name": name,
            "description": "Test group",
            "is_active": True,
            "domain_name": domain_name,
            "total_resource_slots": {},
            "allowed_vfolder_hosts": {},
            "integration_id": None,
            "resource_policy": "default",
            "type": ProjectType.GENERAL,
        }
        await conn.execute(sa.insert(GroupRow).values(group_data))

    try:
        yield group_id
    finally:
        async with database_engine.begin() as conn:
            await conn.execute(sa.delete(GroupRow).where(GroupRow.id == group_id))


async def test_modify_domain_node_scaling_group_overlap_error(
    processors: DomainProcessors, database_engine, superadmin_user
) -> None:
    domain_name = "test-overlap-scaling-groups"
    async with create_domain(database_engine, domain_name):
        action = ModifyDomainNodeAction(
            name=domain_name,
            user_info=superadmin_user,
            modifier=DomainNodeModifier(),
            sgroups_to_add={"sg1", "sg2"},
            sgroups_to_remove={"sg1", "sg3"},
        )

        with pytest.raises(ValueError, match="Should be no scaling group names included"):
            await processors.modify_domain_node.wait_for_complete(action)


async def test_purge_domain_with_active_users_fails(
    processors: DomainProcessors, database_engine, admin_user
) -> None:
    domain_name = "test-purge-with-users"
    async with create_domain(database_engine, domain_name):
        async with create_test_user(database_engine, "test@example.com", domain_name):
            await processors.delete_domain.wait_for_complete(
                DeleteDomainAction(name=domain_name, user_info=admin_user)
            )

            result = await processors.purge_domain.wait_for_complete(
                PurgeDomainAction(name=domain_name, user_info=admin_user)
            )

            assert result.success is False
            assert "users" in result.description.lower()


async def test_purge_domain_with_active_groups_fails(
    processors: DomainProcessors, database_engine, admin_user
) -> None:
    domain_name = "test-purge-with-groups"
    async with create_domain(database_engine, domain_name):
        async with create_test_group(database_engine, "test-group", domain_name):
            await processors.delete_domain.wait_for_complete(
                DeleteDomainAction(name=domain_name, user_info=admin_user)
            )

            result = await processors.purge_domain.wait_for_complete(
                PurgeDomainAction(name=domain_name, user_info=admin_user)
            )

            assert result.success is False
            assert "groups" in result.description.lower()
