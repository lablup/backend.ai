from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

import pytest
import sqlalchemy as sa

from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.models.resource_policy import ProjectResourcePolicyRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.project_resource_policy.repository import (
    ProjectResourcePolicyRepository,
)
from ai.backend.manager.services.project_resource_policy.actions.create_project_resource_policy import (
    CreateProjectResourcePolicyAction,
)
from ai.backend.manager.services.project_resource_policy.actions.delete_project_resource_policy import (
    DeleteProjectResourcePolicyAction,
)
from ai.backend.manager.services.project_resource_policy.actions.modify_project_resource_policy import (
    ModifyProjectResourcePolicyAction,
    ProjectResourcePolicyModifier,
)
from ai.backend.manager.services.project_resource_policy.service import (
    ProjectResourcePolicyService,
)
from ai.backend.manager.services.project_resource_policy.types import (
    ProjectResourcePolicyCreator,
)
from ai.backend.manager.types import OptionalState


@pytest.fixture
def project_resource_policy_repository(
    database_engine: ExtendedAsyncSAEngine,
) -> ProjectResourcePolicyRepository:
    return ProjectResourcePolicyRepository(db=database_engine)


@pytest.fixture
def project_resource_policy_service(
    project_resource_policy_repository: ProjectResourcePolicyRepository,
) -> ProjectResourcePolicyService:
    return ProjectResourcePolicyService(
        project_resource_policy_repository=project_resource_policy_repository
    )


@pytest.fixture
def create_project_resource_policy(
    database_engine: ExtendedAsyncSAEngine,
):
    @asynccontextmanager
    async def _create_project_resource_policy(
        name: str,
        *,
        max_vfolder_count: Optional[int] = 10,
        max_quota_scope_size: Optional[int] = 1073741824,  # 1GB
        max_network_count: Optional[int] = 1,
    ) -> AsyncGenerator[str, None]:
        policy_data = {
            "name": name,
            "max_vfolder_count": max_vfolder_count,
            "max_quota_scope_size": max_quota_scope_size,
            "max_network_count": max_network_count,
        }
        async with database_engine.begin_session() as session:
            await session.execute(sa.insert(ProjectResourcePolicyRow).values(**policy_data))

        try:
            yield name
        finally:
            async with database_engine.begin_session() as session:
                await session.execute(
                    sa.delete(ProjectResourcePolicyRow).where(ProjectResourcePolicyRow.name == name)
                )

    return _create_project_resource_policy


async def test_create_project_resource_policy(
    project_resource_policy_service: ProjectResourcePolicyService,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    action = CreateProjectResourcePolicyAction(
        creator=ProjectResourcePolicyCreator(
            name="test-policy",
            max_vfolder_count=20,
            max_quota_scope_size=2147483648,  # 2GB
            max_vfolder_size=None,  # deprecated field
            max_network_count=5,
        ),
    )

    result = await project_resource_policy_service.create_project_resource_policy(action)

    # Verify the policy was created correctly
    assert result.project_resource_policy.name == "test-policy"
    assert result.project_resource_policy.max_vfolder_count == 20
    assert result.project_resource_policy.max_quota_scope_size == 2147483648
    assert result.project_resource_policy.max_network_count == 5

    # Clean up
    async with database_engine.begin_session() as session:
        await session.execute(
            sa.delete(ProjectResourcePolicyRow).where(
                ProjectResourcePolicyRow.name == "test-policy"
            )
        )


async def test_modify_project_resource_policy(
    project_resource_policy_service: ProjectResourcePolicyService,
    database_engine: ExtendedAsyncSAEngine,
    create_project_resource_policy,
) -> None:
    policy_name = "modify-test-policy"
    async with create_project_resource_policy(
        name=policy_name,
        max_vfolder_count=10,
        max_quota_scope_size=1073741824,
        max_network_count=1,
    ):
        action = ModifyProjectResourcePolicyAction(
            name=policy_name,
            modifier=ProjectResourcePolicyModifier(
                max_vfolder_count=OptionalState.update(30),
                max_quota_scope_size=OptionalState.update(3221225472),  # 3GB
                max_network_count=OptionalState.update(10),
            ),
        )

        result = await project_resource_policy_service.modify_project_resource_policy(action)

        assert result.project_resource_policy.name == policy_name
        assert result.project_resource_policy.max_vfolder_count == 30
        assert result.project_resource_policy.max_quota_scope_size == 3221225472
        assert result.project_resource_policy.max_network_count == 10


async def test_modify_project_resource_policy_not_found(
    project_resource_policy_service: ProjectResourcePolicyService,
) -> None:
    action = ModifyProjectResourcePolicyAction(
        name="non-existent-policy",
        modifier=ProjectResourcePolicyModifier(
            max_vfolder_count=OptionalState.update(30),
        ),
    )

    with pytest.raises(ObjectNotFound) as exc_info:
        await project_resource_policy_service.modify_project_resource_policy(action)

    assert "Project resource policy with name non-existent-policy not found" in str(exc_info.value)


async def test_delete_project_resource_policy(
    project_resource_policy_service: ProjectResourcePolicyService,
    database_engine: ExtendedAsyncSAEngine,
    create_project_resource_policy,
) -> None:
    policy_name = "delete-test-policy"
    async with create_project_resource_policy(name=policy_name) as _:
        action = DeleteProjectResourcePolicyAction(name=policy_name)
        result = await project_resource_policy_service.delete_project_resource_policy(action)

        assert result.project_resource_policy.name == policy_name

        # Verify it's deleted
        async with database_engine.begin_session() as session:
            query = sa.select(ProjectResourcePolicyRow).where(
                ProjectResourcePolicyRow.name == policy_name
            )
            deleted_policy = (await session.execute(query)).scalar_one_or_none()
            assert deleted_policy is None


async def test_delete_project_resource_policy_not_found(
    project_resource_policy_service: ProjectResourcePolicyService,
) -> None:
    action = DeleteProjectResourcePolicyAction(name="non-existent-policy")

    with pytest.raises(ObjectNotFound) as exc_info:
        await project_resource_policy_service.delete_project_resource_policy(action)

    assert "Project resource policy with name non-existent-policy not found" in str(exc_info.value)


async def test_partial_update_project_resource_policy(
    project_resource_policy_service: ProjectResourcePolicyService,
    database_engine: ExtendedAsyncSAEngine,
    create_project_resource_policy,
) -> None:
    policy_name = "partial-update-policy"
    async with create_project_resource_policy(
        name=policy_name,
        max_vfolder_count=10,
        max_quota_scope_size=1073741824,
        max_network_count=1,
    ):
        # Update only max_vfolder_count, leave others unchanged
        action = ModifyProjectResourcePolicyAction(
            name=policy_name,
            modifier=ProjectResourcePolicyModifier(
                max_vfolder_count=OptionalState.update(25),
                # Other fields remain OptionalState.nop() by default
            ),
        )

        result = await project_resource_policy_service.modify_project_resource_policy(action)

        assert result.project_resource_policy.name == policy_name
        assert result.project_resource_policy.max_vfolder_count == 25
        assert result.project_resource_policy.max_quota_scope_size == 1073741824  # Unchanged
        assert result.project_resource_policy.max_network_count == 1  # Unchanged
