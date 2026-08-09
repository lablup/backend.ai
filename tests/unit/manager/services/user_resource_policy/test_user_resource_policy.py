"""The one user-resource-policy operation that still has a service.

Every other operation wires straight to the generic ops services, so what is left
to cover here is the read that resolves the caller's own policy through ``users``.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.identifier.resource_policy import UserResourcePolicyUUID
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.repositories.user_resource_policy.repository import (
    UserResourcePolicyRepository,
)
from ai.backend.manager.services.user_resource_policy.actions.get_my_user_resource_policy import (
    GetMyUserResourcePolicyAction,
)
from ai.backend.manager.services.user_resource_policy.service import UserResourcePolicyService


@pytest.fixture
def mock_repository() -> MagicMock:
    return MagicMock(spec=UserResourcePolicyRepository)


@pytest.fixture
def service(mock_repository: MagicMock) -> UserResourcePolicyService:
    return UserResourcePolicyService(user_resource_policy_repository=mock_repository)


@pytest.fixture
def sample_policy_data() -> UserResourcePolicyData:
    return UserResourcePolicyData(
        uuid=UserResourcePolicyUUID(uuid4()),
        name="test-policy",
        max_vfolder_count=10,
        max_quota_scope_size=1000000,
        max_session_count_per_model_session=5,
        max_customized_image_count=3,
    )


async def test_get_my_user_resource_policy_reads_by_user_id(
    service: UserResourcePolicyService,
    mock_repository: MagicMock,
    sample_policy_data: UserResourcePolicyData,
) -> None:
    """The action carries the user id; the repository resolves the policy from it."""
    user_id = uuid4()
    mock_repository.get_by_user_id = AsyncMock(return_value=sample_policy_data)

    result = await service.get_my_user_resource_policy(
        GetMyUserResourcePolicyAction(user_id=user_id)
    )

    mock_repository.get_by_user_id.assert_awaited_once_with(user_id)
    assert result.data == sample_policy_data


async def test_get_my_user_resource_policy_propagates_the_miss(
    service: UserResourcePolicyService,
    mock_repository: MagicMock,
) -> None:
    """A user with no policy is an error from the repository, not an empty result."""
    mock_repository.get_by_user_id = AsyncMock(side_effect=ValueError("not found"))

    with pytest.raises(ValueError):
        await service.get_my_user_resource_policy(GetMyUserResourcePolicyAction(user_id=uuid4()))
