import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
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
from ai.backend.manager.services.domain.types import DomainData, UserInfo
from ai.backend.manager.types import State, TriState

from .test_utils import TestScenario


@pytest.fixture
def processors(database_fixture, database_engine) -> DomainProcessors:
    domain_service = DomainService(database_engine)
    return DomainProcessors(domain_service)


@pytest.fixture
def admin_user() -> UserInfo:
    return UserInfo(
        id=uuid.UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
        role=UserRole.ADMIN,
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
                name="test-create-domain-node",
                user_info=UserInfo(
                    id=uuid.UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                    role=UserRole.ADMIN,
                    domain_name="default",
                ),
                description="Test domain",
                is_active=True,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
                integration_id=None,
                dotfiles=b"\x90",
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
                name="default",
                user_info=UserInfo(
                    id=uuid.UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                    role=UserRole.ADMIN,
                    domain_name="default",
                ),
                description=None,
                is_active=None,
                total_resource_slots=None,
                allowed_vfolder_hosts=None,
                allowed_docker_registries=None,
                integration_id=None,
                dotfiles=None,
                scaling_groups=None,
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
                    id=uuid.UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                    role=UserRole.SUPERADMIN,
                    domain_name="default",
                ),
                description=TriState("description", State.UPDATE, "Domain Description Modified"),
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
                    id=uuid.UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                    role=UserRole.SUPERADMIN,
                    domain_name="default",
                ),
                description=TriState("description", State.UPDATE, "Domain Description Modified"),
            ),
            ValueError,
        ),
        TestScenario.failure(
            "Modify a domain without enough permission",
            ModifyDomainNodeAction(
                name="not-exist-domain",
                user_info=UserInfo(
                    id=uuid.UUID("dfa9da54-4b28-432f-be29-c0d680c7a412"),
                    role=UserRole.USER,
                    domain_name="default",
                ),
                description=TriState("description", State.UPDATE, "Domain Description Modified"),
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
                name="test-create-domain",
                description="Test domain",
                is_active=True,
                total_resource_slots=ResourceSlot.from_user_input({}, None),
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
                integration_id=None,
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
                name="default",
                description=None,
                is_active=None,
                total_resource_slots=None,
                allowed_vfolder_hosts=None,
                allowed_docker_registries=None,
                integration_id=None,
            ),
            CreateDomainActionResult(
                domain_data=None,
                success=False,
                description="integrity error",
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
    processors: DomainProcessors, database_engine
) -> None:
    domain_name = "test-create-domain-post-func"
    action = CreateDomainAction(
        name=domain_name,
        description=None,
        is_active=None,
        total_resource_slots=None,
        allowed_vfolder_hosts=None,
        allowed_docker_registries=None,
        integration_id=None,
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
        TestScenario.success(
            "Modify domain",
            ModifyDomainAction(
                domain_name="test-modify-domain",
                description=TriState("description", State.UPDATE, "Domain Description Modified"),
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
                description=TriState("description", State.UPDATE, "Domain Description Modified"),
            ),
            ModifyDomainActionResult(
                domain_data=None,
                success=False,
                description="domain not found",
            ),
        ),
    ],
)
async def test_modify_domain(
    processors: DomainProcessors,
    test_scenario: TestScenario[ModifyDomainAction, ModifyDomainActionResult],
    database_engine,
) -> None:
    async with create_domain(database_engine, "test-modify-domain"):
        await test_scenario.test(processors.modify_domain.wait_for_complete)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "Delete a domain",
            DeleteDomainAction(
                name="test-delete-domain",
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
) -> None:
    async with create_domain(database_engine, "test-delete-domain-in-db") as domain_name:
        async with database_engine.begin_session() as session:
            domain = await session.scalar(
                sa.select(DomainRow).where(
                    (DomainRow.name == domain_name) & (DomainRow.is_active == True)  # noqa
                )
            )

        await processors.delete_domain.wait_for_complete(DeleteDomainAction(name=domain_name))

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
async def test_purge_domain_in_db(processors: DomainProcessors, database_engine) -> None:
    domain_name = "test-purge-domain-in-db"
    # create domain
    async with create_domain(database_engine, domain_name):
        # delete domain(soft delete) and delete model-store group
        await processors.delete_domain.wait_for_complete(DeleteDomainAction(name=domain_name))
        async with database_engine.begin_session() as session:
            await session.execute(
                sa.update(GroupRow)
                .where((GroupRow.name == "model-store") & (GroupRow.domain_name == domain_name))
                .values({"is_active": False})
            )

            domain = await session.scalar(sa.select(DomainRow).where(DomainRow.name == domain_name))
            assert domain is not None

        # purge domain
        await processors.purge_domain.wait_for_complete(PurgeDomainAction(name=domain_name))
        async with database_engine.begin_session() as session:
            domain = await session.scalar(sa.select(DomainRow).where(DomainRow.name == domain_name))

            assert domain is None
