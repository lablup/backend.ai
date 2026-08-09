"""The one keypair-resource-policy operation that still has a service.

Create / modify / delete now wire straight to the generic ops services, so what is
left to cover here is the read that resolves the caller's own policy through
``keypairs``.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.identifier.resource_policy import KeyPairResourcePolicyUUID
from ai.backend.common.types import DefaultForUnspecified, ResourceSlot
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.repositories.keypair_resource_policy.repository import (
    KeypairResourcePolicyRepository,
)
from ai.backend.manager.services.keypair_resource_policy.actions.get_my_keypair_resource_policy import (
    GetMyKeypairResourcePolicyAction,
)
from ai.backend.manager.services.keypair_resource_policy.service import (
    KeypairResourcePolicyService,
)


@pytest.fixture
def mock_repository() -> MagicMock:
    return MagicMock(spec=KeypairResourcePolicyRepository)


@pytest.fixture
def service(mock_repository: MagicMock) -> KeypairResourcePolicyService:
    return KeypairResourcePolicyService(keypair_resource_policy_repository=mock_repository)


@pytest.fixture
def sample_policy_data() -> KeyPairResourcePolicyData:
    return KeyPairResourcePolicyData(
        uuid=KeyPairResourcePolicyUUID(uuid4()),
        name="test-policy",
        created_at=None,
        default_for_unspecified=DefaultForUnspecified.LIMITED,
        total_resource_slots=ResourceSlot(),
        max_session_lifetime=0,
        max_concurrent_sessions=10,
        max_pending_session_count=None,
        max_pending_session_resource_slots=None,
        max_priority=None,
        max_concurrent_sftp_sessions=5,
        max_containers_per_session=1,
        idle_timeout=3600,
        allowed_vfolder_hosts={},
    )


async def test_get_my_keypair_resource_policy_reads_by_user_id(
    service: KeypairResourcePolicyService,
    mock_repository: MagicMock,
    sample_policy_data: KeyPairResourcePolicyData,
) -> None:
    """The action carries the user id; the repository resolves the policy from it."""
    user_id = uuid4()
    mock_repository.get_by_user_id = AsyncMock(return_value=sample_policy_data)

    result = await service.get_my_keypair_resource_policy(
        GetMyKeypairResourcePolicyAction(user_id=user_id)
    )

    mock_repository.get_by_user_id.assert_awaited_once_with(user_id)
    assert result.data == sample_policy_data


async def test_get_my_keypair_resource_policy_propagates_the_miss(
    service: KeypairResourcePolicyService,
    mock_repository: MagicMock,
) -> None:
    """A user with no active keypair is an error from the repository."""
    mock_repository.get_by_user_id = AsyncMock(side_effect=ValueError("not found"))

    with pytest.raises(ValueError):
        await service.get_my_keypair_resource_policy(
            GetMyKeypairResourcePolicyAction(user_id=uuid4())
        )
