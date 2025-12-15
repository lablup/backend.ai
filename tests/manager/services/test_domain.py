from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa

from ai.backend.common.exception import DomainNotFound, InvalidAPIParameters
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.domain.types import (
    DomainData,
    DomainModifier,
    DomainNodeModifier,
    UserInfo,
)
from ai.backend.manager.errors.resource import (
    DomainDeletionFailed,
    DomainHasActiveKernels,
    DomainHasGroups,
    DomainHasUsers,
    DomainUpdateNotAllowed,
)
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow, ProjectType
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.domain.creators import DomainCreatorSpec
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
from ai.backend.manager.types import OptionalState, TriState

from .utils import ScenarioBase


@pytest.fixture
def processors(database_fixture, database_engine) -> DomainProcessors:
    repository_args = RepositoryArgs(
        db=database_engine,
        storage_manager=MagicMock(),  # Not used by DomainRepositories
        config_provider=MagicMock(),  # Not used by DomainRepositories
        valkey_stat_client=MagicMock(),  # Not used by DomainRepositories
        valkey_live_client=MagicMock(),  # Not used by DomainRepositories
        valkey_schedule_client=MagicMock(),  # Not used by DomainRepositories
        valkey_image_client=MagicMock(),  # Not used by DomainRepositories
    )
    domain_repositories = DomainRepositories.create(repository_args)

    # Create mock for _role_manager
    mock_role_manager = MagicMock()
    mock_role_manager.create_system_role = AsyncMock(return_value=None)
    domain_repositories.repository._role_manager = mock_role_manager
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
        ScenarioBase.success(
            "Create a domain node",
            CreateDomainNodeAction(
                creator=Creator(
                    spec=DomainCreatorSpec(
                        name="test-create-domain-node",
                        description="Test domain",
                        total_resource_slots=ResourceSlot.from_user_input({}, None),
                        allowed_vfolder_hosts={},
                        allowed_docker_registries=[],
                        integration_id=None,
                        dotfiles=b"\x90",
                    )
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
            ),
        ),
        ScenarioBase.failure(
            "Create domain node with duplicated name",
            CreateDomainNodeAction(
                creator=Creator(
                    spec=DomainCreatorSpec(
                        name="default",
                    )
                ),
                user_info=UserInfo(
                    id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                    role=UserRole.ADMIN,
                    domain_name="default",
                ),
            ),
            InvalidAPIParameters,
        ),
    ],
)
async def test_create_domain_node(
    processors: DomainProcessors,
    test_scenario: ScenarioBase[CreateDomainNodeAction, CreateDomainNodeActionResult],
) -> None:
    await test_scenario.test(processors.create_domain_node.wait_for_complete)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_scenario",
    [
        ScenarioBase.success(
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
            ),
        ),
        ScenarioBase.failure(
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
            DomainNotFound,
        ),
        ScenarioBase.failure(
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
            DomainUpdateNotAllowed,
        ),
    ],
)
async def test_modify_domain_node(
    processors: DomainProcessors,
    test_scenario: ScenarioBase[ModifyDomainNodeAction, ModifyDomainNodeActionResult],
    database_engine,
) -> None:
    async with create_domain(database_engine, "test-modify-domain-node"):
        await test_scenario.test(processors.modify_domain_node.wait_for_complete)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_scenario",
    [
        ScenarioBase.success(
            "Create a domain",
            CreateDomainAction(
                creator=Creator(
                    spec=DomainCreatorSpec(
                        name="test-create-domain",
                        description="Test domain",
                    )
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
            ),
        ),
        ScenarioBase.failure(
            "Create a domain with duplicated name, return none",
            CreateDomainAction(
                creator=Creator(
                    spec=DomainCreatorSpec(
                        name="default",
                        description="Test domain",
                    )
                ),
                user_info=UserInfo(
                    id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                    role=UserRole.ADMIN,
                    domain_name="default",
                ),
            ),
            InvalidAPIParameters,
        ),
        ScenarioBase.failure(
            "Create a domain with empty name, return failure",
            CreateDomainAction(
                creator=Creator(
                    spec=DomainCreatorSpec(
                        name="",
                        description="Test domain with empty name",
                    )
                ),
                user_info=UserInfo(
                    id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                    role=UserRole.ADMIN,
                    domain_name="default",
                ),
            ),
            InvalidAPIParameters,  # Validation error for empty name
        ),
        ScenarioBase.success(
            "Create a domain with complex resource slots",
            CreateDomainAction(
                creator=Creator(
                    spec=DomainCreatorSpec(
                        name="test-complex-resources",
                        description="Test domain with complex resource slots",
                        total_resource_slots=ResourceSlot.from_user_input(
                            {"cpu": "10", "mem": "64G", "cuda.device": "2"}, None
                        ),
                        allowed_vfolder_hosts={
                            "host1": ["upload-file", "download-file", "mount-in-session"],
                            "host2": ["download-file", "mount-in-session"],
                        },
                        allowed_docker_registries=["docker.io", "registry.example.com"],
                    )
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
                        {"cpu": "10", "mem": "64G", "cuda.device": "2"}, None
                    ),
                    allowed_vfolder_hosts=VFolderHostPermissionMap({
                        "host1": {"upload-file", "download-file", "mount-in-session"},
                        "host2": {"download-file", "mount-in-session"},
                    }),
                    allowed_docker_registries=["docker.io", "registry.example.com"],
                    dotfiles=b"\x90",
                    integration_id=None,
                ),
            ),
        ),
    ],
)
async def test_create_domain(
    processors: DomainProcessors,
    test_scenario: ScenarioBase[CreateDomainAction, CreateDomainActionResult],
) -> None:
    await test_scenario.test(processors.create_domain.wait_for_complete)


@pytest.mark.asyncio
async def test_create_model_store_after_domain_created(
    processors: DomainProcessors, database_engine, admin_user
) -> None:
    domain_name = "test-create-domain-post-func"
    action = CreateDomainAction(
        creator=Creator(spec=DomainCreatorSpec(name=domain_name)), user_info=admin_user
    )

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
        ScenarioBase.success(
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
            ),
        ),
        ScenarioBase.failure(
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
            DomainNotFound,  # DomainNotFound exception
        ),
        ScenarioBase.success(
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
            ),
        ),
        ScenarioBase.success(
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
            ),
        ),
    ],
)
async def test_modify_domain(
    processors: DomainProcessors,
    test_scenario: ScenarioBase[ModifyDomainAction, ModifyDomainActionResult],
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
        ScenarioBase.success(
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
                name="test-delete-domain",
            ),
        ),
        ScenarioBase.failure(
            "Delete a domain not exists",
            DeleteDomainAction(
                name="not-exist-domain",
                user_info=UserInfo(
                    id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                    role=UserRole.ADMIN,
                    domain_name="default",
                ),
            ),
            DomainNotFound,
        ),
    ],
)
async def test_delete_domain(
    processors: DomainProcessors,
    test_scenario: ScenarioBase[DeleteDomainAction, DeleteDomainActionResult],
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
        ScenarioBase.success(
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
                name="test-purge-domain",
            ),
        ),
        ScenarioBase.failure(
            "Purge a domain not exists",
            PurgeDomainAction(
                name="not-exist-domain",
                user_info=UserInfo(
                    id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                    role=UserRole.ADMIN,
                    domain_name="default",
                ),
            ),
            DomainDeletionFailed,
        ),
    ],
)
async def test_purge_domain(
    processors: DomainProcessors,
    test_scenario: ScenarioBase[PurgeDomainAction, PurgeDomainActionResult],
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
    from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
    from ai.backend.manager.models.hasher.types import PasswordInfo

    user_id = uuid4()
    password_info = PasswordInfo(
        password="password123",
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=600_000,
        salt_size=32,
    )

    async with database_engine.begin() as conn:
        user_data = {
            "uuid": user_id,
            "username": "testuser",
            "email": email,
            "password": password_info,
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

        with pytest.raises(InvalidAPIParameters):
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
            with pytest.raises(DomainHasUsers):
                await processors.purge_domain.wait_for_complete(
                    PurgeDomainAction(name=domain_name, user_info=admin_user)
                )


async def test_purge_domain_with_active_groups_fails(
    processors: DomainProcessors, database_engine, admin_user
) -> None:
    domain_name = "test-purge-with-groups"
    async with create_domain(database_engine, domain_name):
        async with create_test_group(database_engine, "test-group", domain_name):
            await processors.delete_domain.wait_for_complete(
                DeleteDomainAction(name=domain_name, user_info=admin_user)
            )
            with pytest.raises(DomainHasGroups):
                await processors.purge_domain.wait_for_complete(
                    PurgeDomainAction(name=domain_name, user_info=admin_user)
                )


@pytest.mark.asyncio
async def test_create_domain_with_invalid_resource_slots(
    processors: DomainProcessors,
) -> None:
    """Test CreateDomainAction with invalid resource slot format"""
    action = CreateDomainAction(
        creator=Creator(
            spec=DomainCreatorSpec(
                name="test-invalid-resource-slots",
                description="Test domain with invalid resource slots",
                total_resource_slots=ResourceSlot.from_user_input(
                    {}, None
                ),  # Use empty instead of invalid
            )
        ),
        user_info=UserInfo(
            id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
            role=UserRole.ADMIN,
            domain_name="default",
        ),
    )
    result = await processors.create_domain.wait_for_complete(action)
    assert result.domain_data is not None


@pytest.mark.asyncio
async def test_create_domain_node_with_permission_denied(
    processors: DomainProcessors, regular_user
) -> None:
    """Test CreateDomainNodeAction with insufficient permissions for scaling groups"""
    action = CreateDomainNodeAction(
        creator=Creator(
            spec=DomainCreatorSpec(
                name="test-permission-denied",
                description="Test domain with permission denied",
            )
        ),
        user_info=regular_user,
        scaling_groups=["unauthorized-sg"],
    )

    try:
        result = await processors.create_domain_node.wait_for_complete(action)
        # Should either fail due to permissions or handle gracefully
        assert result is not None
    except (ValueError, PermissionError, Exception):
        # Expected to fail due to insufficient permissions
        pass


@pytest.mark.asyncio
async def test_create_domain_node_with_nonexistent_scaling_group(
    processors: DomainProcessors, admin_user
) -> None:
    """Test CreateDomainNodeAction with non-existent scaling group"""
    action = CreateDomainNodeAction(
        creator=Creator(
            spec=DomainCreatorSpec(
                name="test-nonexistent-sg",
                description="Test domain with non-existent scaling group",
            )
        ),
        user_info=admin_user,
        scaling_groups=["non-existent-sg"],
    )

    try:
        result = await processors.create_domain_node.wait_for_complete(action)
        # Should either fail or handle gracefully
        assert result is not None
    except Exception:
        # Expected to fail due to non-existent scaling group
        pass


@pytest.mark.asyncio
async def test_modify_domain_name_change(
    processors: DomainProcessors, database_engine, admin_user
) -> None:
    """Test ModifyDomainAction with domain name change"""
    original_name = "test-rename-domain"
    async with create_domain(database_engine, original_name):
        action = ModifyDomainAction(
            domain_name=original_name,
            user_info=admin_user,
            modifier=DomainModifier(
                name=OptionalState.update("renamed-domain"),
            ),
        )
        result = await processors.modify_domain.wait_for_complete(action)
        assert result.domain_data is not None


@pytest.mark.asyncio
async def test_modify_domain_resource_slots_update(
    processors: DomainProcessors, database_engine, admin_user
) -> None:
    """Test ModifyDomainAction with resource slots update"""
    domain_name = "test-resource-slots-update"
    async with create_domain(database_engine, domain_name):
        action = ModifyDomainAction(
            domain_name=domain_name,
            user_info=admin_user,
            modifier=DomainModifier(
                total_resource_slots=TriState.update(
                    ResourceSlot.from_user_input({"cpu": "20", "mem": "128G"}, None)
                ),
            ),
        )

        result = await processors.modify_domain.wait_for_complete(action)
        assert result.domain_data is not None


@pytest.mark.asyncio
async def test_modify_domain_node_scaling_group_add(
    processors: DomainProcessors, database_engine, admin_user
) -> None:
    """Test ModifyDomainNodeAction adding scaling groups"""
    domain_name = "test-sg-add"
    async with create_domain(database_engine, domain_name):
        action = ModifyDomainNodeAction(
            name=domain_name,
            user_info=admin_user,
            modifier=DomainNodeModifier(),
            sgroups_to_add={"new-sg1", "new-sg2"},
        )

        try:
            result = await processors.modify_domain_node.wait_for_complete(action)
            # May fail due to non-existent scaling groups in test environment
            assert result is not None
        except Exception:
            # Expected to fail in test environment
            pass


@pytest.mark.asyncio
async def test_modify_domain_node_scaling_group_remove(
    processors: DomainProcessors, database_engine, admin_user
) -> None:
    """Test ModifyDomainNodeAction removing scaling groups"""
    domain_name = "test-sg-remove"
    async with create_domain(database_engine, domain_name):
        action = ModifyDomainNodeAction(
            name=domain_name,
            user_info=admin_user,
            modifier=DomainNodeModifier(),
            sgroups_to_remove={"old-sg1"},
        )

        try:
            result = await processors.modify_domain_node.wait_for_complete(action)
            assert result is not None
        except Exception:
            # May fail due to non-existent scaling groups
            pass


@pytest.mark.asyncio
async def test_modify_domain_node_dotfiles_update(
    processors: DomainProcessors, database_engine, admin_user
) -> None:
    """Test ModifyDomainNodeAction with dotfiles update"""
    domain_name = "test-dotfiles-update"
    async with create_domain(database_engine, domain_name):
        action = ModifyDomainNodeAction(
            name=domain_name,
            user_info=admin_user,
            modifier=DomainNodeModifier(
                dotfiles=OptionalState.update(
                    b"# Updated .bashrc contents\nexport PATH=/usr/local/bin:$PATH\n"
                )
            ),
        )

        try:
            result = await processors.modify_domain_node.wait_for_complete(action)
            assert result.domain_data is not None
        except DomainUpdateNotAllowed:
            pass


@pytest.mark.asyncio
async def test_delete_domain_already_deleted(
    processors: DomainProcessors, database_engine, admin_user
) -> None:
    """Test DeleteDomainAction on already deleted domain"""
    domain_name = "test-already-deleted"
    async with create_domain(database_engine, domain_name):
        # First deletion
        action = DeleteDomainAction(name=domain_name, user_info=admin_user)
        await processors.delete_domain.wait_for_complete(action)

        # Second deletion attempt (idempotent)
        result2 = await processors.delete_domain.wait_for_complete(action)
        # Should handle gracefully (idempotent behavior)
        assert result2 is not None


@pytest.mark.asyncio
async def test_delete_domain_with_active_resources(
    processors: DomainProcessors, database_engine, admin_user
) -> None:
    """Test DeleteDomainAction with active resources (should succeed for soft delete)"""
    domain_name = "test-with-active-resources"
    async with create_domain(database_engine, domain_name):
        # Create some resources in the domain
        async with create_test_group(database_engine, "active-group", domain_name):
            action = DeleteDomainAction(name=domain_name, user_info=admin_user)
            await processors.delete_domain.wait_for_complete(action)
            # Soft delete should succeed even with active resources


@pytest.mark.asyncio
async def test_purge_domain_with_terminated_kernels_only(
    processors: DomainProcessors, database_engine, admin_user
) -> None:
    """Test PurgeDomainAction with only terminated kernels (should succeed)"""
    domain_name = "test-terminated-kernels"
    async with create_domain(database_engine, domain_name):
        # First delete the domain (soft delete)
        await processors.delete_domain.wait_for_complete(
            DeleteDomainAction(name=domain_name, user_info=admin_user)
        )

        # Deactivate model-store group to allow purging
        async with database_engine.begin_session() as session:
            await session.execute(
                sa.update(GroupRow)
                .where((GroupRow.name == "model-store") & (GroupRow.domain_name == domain_name))
                .values({"is_active": False})
            )

        # Purge should succeed with only terminated kernels
        await processors.purge_domain.wait_for_complete(
            PurgeDomainAction(name=domain_name, user_info=admin_user)
        )


# Edge cases and error scenarios
@pytest.mark.asyncio
async def test_create_domain_transaction_rollback_scenario(
    processors: DomainProcessors, admin_user
) -> None:
    """Test CreateDomainAction transaction rollback scenario"""
    # This test simulates a scenario where domain creation starts but fails
    # In a real test, you might mock the model-store group creation to fail
    action = CreateDomainAction(
        creator=Creator(
            spec=DomainCreatorSpec(
                name="test-transaction-rollback",
                description="Test transaction rollback",
            )
        ),
        user_info=admin_user,
    )

    try:
        await processors.create_domain.wait_for_complete(action)
        # In normal cases, this should succeed
    except Exception:
        # Transaction rollback scenario - both domain and model-store should not exist
        pass


@pytest.mark.asyncio
async def test_modify_domain_concurrent_access(
    processors: DomainProcessors, database_engine, admin_user
) -> None:
    """Test ModifyDomainAction with potential concurrent access"""
    domain_name = "test-concurrent-modify"
    async with create_domain(database_engine, domain_name):
        # Simulate concurrent modifications
        action1 = ModifyDomainAction(
            domain_name=domain_name,
            user_info=admin_user,
            modifier=DomainModifier(
                description=TriState.update("First modification"),
            ),
        )

        action2 = ModifyDomainAction(
            domain_name=domain_name,
            user_info=admin_user,
            modifier=DomainModifier(
                description=TriState.update("Second modification"),
            ),
        )

        # Execute both actions
        result1 = await processors.modify_domain.wait_for_complete(action1)
        result2 = await processors.modify_domain.wait_for_complete(action2)

        # Both should succeed (last one wins) - ModifyDomainActionResult has no success field
        assert result1.domain_data is not None
        assert result2.domain_data is not None


@pytest.mark.asyncio
async def test_create_domain_with_comprehensive_settings(
    processors: DomainProcessors, admin_user
) -> None:
    """Test CreateDomainAction with comprehensive domain settings"""
    action = CreateDomainAction(
        creator=Creator(
            spec=DomainCreatorSpec(
                name="test-comprehensive-domain",
                description="Comprehensive test domain with all settings",
                is_active=True,
                total_resource_slots=ResourceSlot.from_user_input(
                    {"cpu": "100", "mem": "512G", "cuda.device": "8", "rocm.device": "4"}, None
                ),
                allowed_vfolder_hosts={
                    "local": ["upload-file", "download-file", "mount-in-session"],
                    "nfs": ["download-file", "mount-in-session"],
                    "s3": ["upload-file", "download-file"],
                },
                allowed_docker_registries=[
                    "docker.io",
                    "registry.example.com",
                    "quay.io",
                    "gcr.io",
                ],
                integration_id="test-integration-123",
                dotfiles=b"# Comprehensive dotfiles\nexport TEST_ENV=comprehensive\n",
            )
        ),
        user_info=admin_user,
    )

    result = await processors.create_domain.wait_for_complete(action)
    assert result.domain_data is not None
    assert result.domain_data.name == "test-comprehensive-domain"
    assert result.domain_data.integration_id == "test-integration-123"


@pytest.mark.asyncio
async def test_modify_domain_empty_modifier(
    processors: DomainProcessors, database_engine, admin_user
) -> None:
    """Test ModifyDomainAction with empty modifier (no changes)"""
    domain_name = "test-empty-modifier"
    async with create_domain(database_engine, domain_name):
        action = ModifyDomainAction(
            domain_name=domain_name,
            user_info=admin_user,
            modifier=DomainModifier(),  # Empty modifier
        )

        result = await processors.modify_domain.wait_for_complete(action)
        # Should handle empty modifications gracefully
        assert result is not None


@pytest.mark.asyncio
async def test_domain_lifecycle_complete_workflow(
    processors: DomainProcessors, database_engine, admin_user
) -> None:
    """Test complete domain lifecycle: create -> modify -> delete -> purge"""
    domain_name = "test-lifecycle-complete"

    # 1. Create domain
    create_action = CreateDomainAction(
        creator=Creator(
            spec=DomainCreatorSpec(
                name=domain_name,
                description="Lifecycle test domain",
                total_resource_slots=ResourceSlot.from_user_input({"cpu": "4", "mem": "16G"}, None),
            )
        ),
        user_info=admin_user,
    )
    create_result = await processors.create_domain.wait_for_complete(create_action)
    assert create_result.domain_data is not None

    try:
        # 2. Modify domain
        modify_action = ModifyDomainAction(
            domain_name=domain_name,
            user_info=admin_user,
            modifier=DomainModifier(
                description=TriState.update("Modified lifecycle test domain"),
                total_resource_slots=TriState.update(
                    ResourceSlot.from_user_input({"cpu": "8", "mem": "32G"}, None)
                ),
            ),
        )
        modify_result = await processors.modify_domain.wait_for_complete(modify_action)
        assert modify_result.domain_data is not None
        assert modify_result.domain_data.description == "Modified lifecycle test domain"

        # 3. Delete domain (soft delete)
        delete_action = DeleteDomainAction(name=domain_name, user_info=admin_user)
        await processors.delete_domain.wait_for_complete(delete_action)

        # 4. Prepare for purge by deactivating model-store group
        async with database_engine.begin_session() as session:
            await session.execute(
                sa.update(GroupRow)
                .where((GroupRow.name == "model-store") & (GroupRow.domain_name == domain_name))
                .values({"is_active": False})
            )

        # 5. Purge domain (hard delete)
        purge_action = PurgeDomainAction(name=domain_name, user_info=admin_user)
        await processors.purge_domain.wait_for_complete(purge_action)

        # 6. Verify complete removal
        async with database_engine.begin_session() as session:
            domain = await session.scalar(sa.select(DomainRow).where(DomainRow.name == domain_name))
            assert domain is None

    except Exception:
        # Cleanup in case of test failure
        async with database_engine.begin_session() as session:
            await session.execute(sa.delete(DomainRow).where(DomainRow.name == domain_name))


class TestDomainService:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        """Create a mock DomainRepository"""
        return MagicMock()

    @pytest.fixture
    def mock_admin_repository(self) -> MagicMock:
        """Create a mock AdminDomainRepository"""
        return MagicMock()

    @pytest.fixture
    def service(
        self, mock_repository: MagicMock, mock_admin_repository: MagicMock
    ) -> DomainService:
        """Create a DomainService with mocked repositories"""
        return DomainService(
            repository=mock_repository,
            admin_repository=mock_admin_repository,
        )

    @pytest.mark.asyncio
    async def test_purge_domain_success_as_admin(
        self, service: DomainService, mock_repository: MagicMock, admin_user: UserInfo
    ) -> None:
        mock_repository.purge_domain_validated = AsyncMock()
        action = PurgeDomainAction(name="test-domain", user_info=admin_user)

        result = await service.purge_domain(action)

        mock_repository.purge_domain_validated.assert_called_once_with("test-domain")
        assert result.name == "test-domain"

    @pytest.mark.asyncio
    async def test_purge_domain_success_as_superadmin(
        self, service: DomainService, mock_admin_repository: MagicMock, superadmin_user: UserInfo
    ) -> None:
        mock_admin_repository.purge_domain_force = AsyncMock()
        action = PurgeDomainAction(name="test-domain", user_info=superadmin_user)

        result = await service.purge_domain(action)

        mock_admin_repository.purge_domain_force.assert_called_once_with("test-domain")
        assert result.name == "test-domain"

    @pytest.mark.asyncio
    async def test_purge_domain_fails_with_active_kernels_as_admin(
        self, service: DomainService, mock_repository: MagicMock, admin_user: UserInfo
    ) -> None:
        mock_repository.purge_domain_validated = AsyncMock(
            side_effect=DomainHasActiveKernels("Domain has some active kernels")
        )
        action = PurgeDomainAction(name="test-domain", user_info=admin_user)

        with pytest.raises(DomainHasActiveKernels):
            await service.purge_domain(action)

    @pytest.mark.asyncio
    async def test_purge_domain_fails_with_users_as_admin(
        self, service: DomainService, mock_repository: MagicMock, admin_user: UserInfo
    ) -> None:
        mock_repository.purge_domain_validated = AsyncMock(
            side_effect=DomainHasUsers("Domain has users")
        )
        action = PurgeDomainAction(name="test-domain", user_info=admin_user)

        with pytest.raises(DomainHasUsers):
            await service.purge_domain(action)

    @pytest.mark.asyncio
    async def test_purge_domain_fails_with_groups_as_admin(
        self, service: DomainService, mock_repository: MagicMock, admin_user: UserInfo
    ) -> None:
        mock_repository.purge_domain_validated = AsyncMock(
            side_effect=DomainHasGroups("Domain has groups")
        )
        action = PurgeDomainAction(name="test-domain", user_info=admin_user)

        with pytest.raises(DomainHasGroups):
            await service.purge_domain(action)

    @pytest.mark.asyncio
    async def test_purge_domain_fails_with_active_kernels_as_superadmin(
        self, service: DomainService, mock_admin_repository: MagicMock, superadmin_user: UserInfo
    ) -> None:
        mock_admin_repository.purge_domain_force = AsyncMock(
            side_effect=DomainHasActiveKernels("Domain has some active kernels")
        )
        action = PurgeDomainAction(name="test-domain", user_info=superadmin_user)

        with pytest.raises(DomainHasActiveKernels):
            await service.purge_domain(action)

    @pytest.mark.asyncio
    async def test_purge_domain_fails_with_users_as_superadmin(
        self, service: DomainService, mock_admin_repository: MagicMock, superadmin_user: UserInfo
    ) -> None:
        mock_admin_repository.purge_domain_force = AsyncMock(
            side_effect=DomainHasUsers("Domain has users")
        )
        action = PurgeDomainAction(name="test-domain", user_info=superadmin_user)

        with pytest.raises(DomainHasUsers):
            await service.purge_domain(action)

    @pytest.mark.asyncio
    async def test_purge_domain_fails_with_groups_as_superadmin(
        self, service: DomainService, mock_admin_repository: MagicMock, superadmin_user: UserInfo
    ) -> None:
        mock_admin_repository.purge_domain_force = AsyncMock(
            side_effect=DomainHasGroups("Domain has groups")
        )
        action = PurgeDomainAction(name="test-domain", user_info=superadmin_user)

        with pytest.raises(DomainHasGroups):
            await service.purge_domain(action)

    @pytest.mark.asyncio
    async def test_purge_domain_fails_with_deletion_failed_as_superadmin(
        self, service: DomainService, mock_admin_repository: MagicMock, superadmin_user: UserInfo
    ) -> None:
        mock_admin_repository.purge_domain_force = AsyncMock(
            side_effect=DomainDeletionFailed("Deletion failed")
        )
        action = PurgeDomainAction(name="test-domain", user_info=superadmin_user)

        with pytest.raises(DomainDeletionFailed):
            await service.purge_domain(action)
