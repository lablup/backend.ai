"""
Mock-based unit tests for KeypairResourcePolicyService.

Tests verify service layer business logic using mocked repository.
Repository tests verify actual DB operations separately.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.exception import KeypairResourcePolicyNotFound
from ai.backend.common.types import DefaultForUnspecified, ResourceSlot
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.keypair_resource_policy.creators import (
    KeyPairResourcePolicyCreatorSpec,
)
from ai.backend.manager.repositories.keypair_resource_policy.repository import (
    KeypairResourcePolicyRepository,
)
from ai.backend.manager.repositories.keypair_resource_policy.updaters import (
    KeyPairResourcePolicyUpdaterSpec,
)
from ai.backend.manager.services.keypair_resource_policy.actions.create_keypair_resource_policy import (
    CreateKeyPairResourcePolicyAction,
)
from ai.backend.manager.services.keypair_resource_policy.actions.delete_keypair_resource_policy import (
    DeleteKeyPairResourcePolicyAction,
)
from ai.backend.manager.services.keypair_resource_policy.actions.modify_keypair_resource_policy import (
    ModifyKeyPairResourcePolicyAction,
)
from ai.backend.manager.services.keypair_resource_policy.service import (
    KeypairResourcePolicyService,
)
from ai.backend.manager.types import OptionalState, TriState


class TestCreateKeypairResourcePolicy:
    """Tests for KeypairResourcePolicyService.create_keypair_resource_policy"""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        return MagicMock(spec=KeypairResourcePolicyRepository)

    @pytest.fixture
    def service(self, mock_repository: MagicMock) -> KeypairResourcePolicyService:
        return KeypairResourcePolicyService(keypair_resource_policy_repository=mock_repository)

    @pytest.fixture
    def sample_policy_data(self) -> KeyPairResourcePolicyData:
        return KeyPairResourcePolicyData(
            name="test-policy",
            created_at=datetime.now(),
            default_for_unspecified=DefaultForUnspecified.LIMITED,
            total_resource_slots=ResourceSlot.from_user_input({"cpu": "2", "mem": "4g"}, None),
            max_session_lifetime=1800,
            max_concurrent_sessions=3,
            max_pending_session_count=5,
            max_pending_session_resource_slots=ResourceSlot.from_user_input(
                {"cpu": "1", "mem": "2g"}, None
            ),
            max_concurrent_sftp_sessions=2,
            max_containers_per_session=1,
            idle_timeout=900,
            allowed_vfolder_hosts={"local": set()},
        )

    @pytest.fixture
    def minimal_policy_data(self) -> KeyPairResourcePolicyData:
        return KeyPairResourcePolicyData(
            name="minimal-policy",
            created_at=datetime.now(),
            default_for_unspecified=DefaultForUnspecified.LIMITED,
            total_resource_slots=ResourceSlot.from_user_input({"cpu": "1", "mem": "1g"}, None),
            max_session_lifetime=0,
            max_concurrent_sessions=1,
            max_pending_session_count=None,
            max_pending_session_resource_slots=None,
            max_concurrent_sftp_sessions=1,
            max_containers_per_session=1,
            idle_timeout=1800,
            allowed_vfolder_hosts={},
        )

    async def test_create_with_valid_data_returns_policy(
        self,
        service: KeypairResourcePolicyService,
        mock_repository: MagicMock,
        sample_policy_data: KeyPairResourcePolicyData,
    ) -> None:
        """Create keypair resource policy with valid data should return the created policy."""
        mock_repository.create_keypair_resource_policy = AsyncMock(return_value=sample_policy_data)

        action = CreateKeyPairResourcePolicyAction(
            creator=Creator(
                spec=KeyPairResourcePolicyCreatorSpec(
                    name=sample_policy_data.name,
                    default_for_unspecified=sample_policy_data.default_for_unspecified,
                    total_resource_slots=sample_policy_data.total_resource_slots,
                    max_session_lifetime=sample_policy_data.max_session_lifetime,
                    max_concurrent_sessions=sample_policy_data.max_concurrent_sessions,
                    max_pending_session_count=sample_policy_data.max_pending_session_count,
                    max_pending_session_resource_slots=sample_policy_data.max_pending_session_resource_slots,
                    max_concurrent_sftp_sessions=sample_policy_data.max_concurrent_sftp_sessions,
                    max_containers_per_session=sample_policy_data.max_containers_per_session,
                    idle_timeout=sample_policy_data.idle_timeout,
                    allowed_vfolder_hosts={"local": {}},
                    max_vfolder_count=3,
                    max_vfolder_size=500,
                    max_quota_scope_size=250,
                )
            )
        )

        result = await service.create_keypair_resource_policy(action)

        assert result.keypair_resource_policy.name == sample_policy_data.name
        assert (
            result.keypair_resource_policy.max_concurrent_sessions
            == sample_policy_data.max_concurrent_sessions
        )
        mock_repository.create_keypair_resource_policy.assert_called_once_with(action.creator)

    async def test_create_with_minimal_config_returns_policy(
        self,
        service: KeypairResourcePolicyService,
        mock_repository: MagicMock,
        minimal_policy_data: KeyPairResourcePolicyData,
    ) -> None:
        """Create keypair resource policy with minimal configuration should succeed."""
        mock_repository.create_keypair_resource_policy = AsyncMock(return_value=minimal_policy_data)

        action = CreateKeyPairResourcePolicyAction(
            creator=Creator(
                spec=KeyPairResourcePolicyCreatorSpec(
                    name=minimal_policy_data.name,
                    allowed_vfolder_hosts={},
                    default_for_unspecified=minimal_policy_data.default_for_unspecified,
                    idle_timeout=minimal_policy_data.idle_timeout,
                    max_concurrent_sessions=minimal_policy_data.max_concurrent_sessions,
                    max_containers_per_session=minimal_policy_data.max_containers_per_session,
                    max_pending_session_count=None,
                    max_pending_session_resource_slots=None,
                    max_quota_scope_size=None,
                    max_vfolder_count=None,
                    max_vfolder_size=None,
                    max_concurrent_sftp_sessions=minimal_policy_data.max_concurrent_sftp_sessions,
                    max_session_lifetime=minimal_policy_data.max_session_lifetime,
                    total_resource_slots=minimal_policy_data.total_resource_slots,
                )
            )
        )

        result = await service.create_keypair_resource_policy(action)

        assert result.keypair_resource_policy.name == minimal_policy_data.name
        assert result.keypair_resource_policy.max_pending_session_count is None

    async def test_create_with_duplicate_name_raises_error(
        self,
        service: KeypairResourcePolicyService,
        mock_repository: MagicMock,
    ) -> None:
        """Create keypair resource policy with duplicate name should raise an error."""
        mock_repository.create_keypair_resource_policy = AsyncMock(
            side_effect=Exception("Duplicate key violation")
        )

        action = CreateKeyPairResourcePolicyAction(
            creator=Creator(
                spec=KeyPairResourcePolicyCreatorSpec(
                    name="existing-policy",
                    allowed_vfolder_hosts=None,
                    default_for_unspecified=DefaultForUnspecified.LIMITED,
                    idle_timeout=None,
                    max_concurrent_sessions=None,
                    max_containers_per_session=None,
                    max_pending_session_count=None,
                    max_pending_session_resource_slots=None,
                    max_quota_scope_size=None,
                    max_vfolder_count=None,
                    max_vfolder_size=None,
                    max_concurrent_sftp_sessions=None,
                    max_session_lifetime=None,
                    total_resource_slots=None,
                )
            )
        )

        with pytest.raises(Exception, match="Duplicate key"):
            await service.create_keypair_resource_policy(action)


class TestModifyKeypairResourcePolicy:
    """Tests for KeypairResourcePolicyService.modify_keypair_resource_policy"""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        return MagicMock(spec=KeypairResourcePolicyRepository)

    @pytest.fixture
    def service(self, mock_repository: MagicMock) -> KeypairResourcePolicyService:
        return KeypairResourcePolicyService(keypair_resource_policy_repository=mock_repository)

    @pytest.fixture
    def modified_policy_data(self) -> KeyPairResourcePolicyData:
        return KeyPairResourcePolicyData(
            name="test-policy",
            created_at=datetime.now(),
            default_for_unspecified=DefaultForUnspecified.LIMITED,
            total_resource_slots=ResourceSlot.from_user_input({"cpu": "4", "mem": "8g"}, None),
            max_session_lifetime=0,
            max_concurrent_sessions=10,
            max_pending_session_count=20,
            max_pending_session_resource_slots=None,
            max_concurrent_sftp_sessions=10,
            max_containers_per_session=3,
            idle_timeout=3600,
            allowed_vfolder_hosts={"shared": set()},
        )

    @pytest.fixture
    def nullified_policy_data(self) -> KeyPairResourcePolicyData:
        return KeyPairResourcePolicyData(
            name="test-policy",
            created_at=datetime.now(),
            default_for_unspecified=DefaultForUnspecified.LIMITED,
            total_resource_slots=ResourceSlot.from_user_input({"cpu": "4", "mem": "8g"}, None),
            max_session_lifetime=0,
            max_concurrent_sessions=30,
            max_pending_session_count=None,
            max_pending_session_resource_slots=None,
            max_concurrent_sftp_sessions=10,
            max_containers_per_session=1,
            idle_timeout=1800,
            allowed_vfolder_hosts={},
        )

    async def test_modify_with_valid_data_returns_updated_policy(
        self,
        service: KeypairResourcePolicyService,
        mock_repository: MagicMock,
        modified_policy_data: KeyPairResourcePolicyData,
    ) -> None:
        """Modify keypair resource policy with valid data should return updated policy."""
        mock_repository.update_keypair_resource_policy = AsyncMock(
            return_value=modified_policy_data
        )

        action = ModifyKeyPairResourcePolicyAction(
            name=modified_policy_data.name,
            updater=Updater(
                spec=KeyPairResourcePolicyUpdaterSpec(
                    max_concurrent_sessions=OptionalState.update(10),
                    idle_timeout=OptionalState.update(3600),
                    max_containers_per_session=OptionalState.update(3),
                    max_pending_session_count=TriState.update(20),
                    allowed_vfolder_hosts=OptionalState.update({"shared": set()}),
                ),
                pk_value=modified_policy_data.name,
            ),
        )

        result = await service.modify_keypair_resource_policy(action)

        assert (
            result.keypair_resource_policy.max_concurrent_sessions
            == modified_policy_data.max_concurrent_sessions
        )
        assert result.keypair_resource_policy.idle_timeout == modified_policy_data.idle_timeout
        mock_repository.update_keypair_resource_policy.assert_called_once_with(action.updater)

    async def test_modify_with_tristate_nullify_returns_policy(
        self,
        service: KeypairResourcePolicyService,
        mock_repository: MagicMock,
        nullified_policy_data: KeyPairResourcePolicyData,
    ) -> None:
        """Modify keypair resource policy with tristate nullify should set fields to None."""
        mock_repository.update_keypair_resource_policy = AsyncMock(
            return_value=nullified_policy_data
        )

        action = ModifyKeyPairResourcePolicyAction(
            name=nullified_policy_data.name,
            updater=Updater(
                spec=KeyPairResourcePolicyUpdaterSpec(
                    max_pending_session_count=TriState.nullify(),
                    max_pending_session_resource_slots=TriState.nullify(),
                ),
                pk_value=nullified_policy_data.name,
            ),
        )

        result = await service.modify_keypair_resource_policy(action)

        assert result.keypair_resource_policy.max_pending_session_count is None
        assert result.keypair_resource_policy.max_pending_session_resource_slots is None

    async def test_modify_with_resource_slots_replacement_returns_policy(
        self,
        service: KeypairResourcePolicyService,
        mock_repository: MagicMock,
    ) -> None:
        """Modify keypair resource policy with resource slots replacement should succeed."""
        new_slots = ResourceSlot.from_user_input({"cpu": "100", "mem": "512g", "gpu": "8"}, None)
        expected_policy = KeyPairResourcePolicyData(
            name="test-policy",
            created_at=datetime.now(),
            default_for_unspecified=DefaultForUnspecified.LIMITED,
            total_resource_slots=new_slots,
            max_session_lifetime=0,
            max_concurrent_sessions=30,
            max_pending_session_count=None,
            max_pending_session_resource_slots=None,
            max_concurrent_sftp_sessions=10,
            max_containers_per_session=1,
            idle_timeout=1800,
            allowed_vfolder_hosts={},
        )
        mock_repository.update_keypair_resource_policy = AsyncMock(return_value=expected_policy)

        action = ModifyKeyPairResourcePolicyAction(
            name="test-policy",
            updater=Updater(
                spec=KeyPairResourcePolicyUpdaterSpec(
                    total_resource_slots=OptionalState.update(new_slots),
                ),
                pk_value="test-policy",
            ),
        )

        result = await service.modify_keypair_resource_policy(action)

        assert result.keypair_resource_policy.total_resource_slots == new_slots

    async def test_modify_nonexistent_raises_not_found(
        self,
        service: KeypairResourcePolicyService,
        mock_repository: MagicMock,
    ) -> None:
        """Modify non-existent keypair resource policy should raise KeypairResourcePolicyNotFound."""
        mock_repository.update_keypair_resource_policy = AsyncMock(
            side_effect=KeypairResourcePolicyNotFound("Policy not found")
        )

        action = ModifyKeyPairResourcePolicyAction(
            name="non-existent-policy",
            updater=Updater(
                spec=KeyPairResourcePolicyUpdaterSpec(
                    max_concurrent_sessions=OptionalState.update(5),
                ),
                pk_value="non-existent-policy",
            ),
        )

        with pytest.raises(KeypairResourcePolicyNotFound):
            await service.modify_keypair_resource_policy(action)


class TestDeleteKeypairResourcePolicy:
    """Tests for KeypairResourcePolicyService.delete_keypair_resource_policy"""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        return MagicMock(spec=KeypairResourcePolicyRepository)

    @pytest.fixture
    def service(self, mock_repository: MagicMock) -> KeypairResourcePolicyService:
        return KeypairResourcePolicyService(keypair_resource_policy_repository=mock_repository)

    @pytest.fixture
    def sample_policy_data(self) -> KeyPairResourcePolicyData:
        return KeyPairResourcePolicyData(
            name="test-policy",
            created_at=datetime.now(),
            default_for_unspecified=DefaultForUnspecified.LIMITED,
            total_resource_slots=ResourceSlot.from_user_input({"cpu": "4", "mem": "8g"}, None),
            max_session_lifetime=0,
            max_concurrent_sessions=30,
            max_pending_session_count=None,
            max_pending_session_resource_slots=None,
            max_concurrent_sftp_sessions=10,
            max_containers_per_session=1,
            idle_timeout=1800,
            allowed_vfolder_hosts={},
        )

    async def test_delete_existing_returns_deleted_policy(
        self,
        service: KeypairResourcePolicyService,
        mock_repository: MagicMock,
        sample_policy_data: KeyPairResourcePolicyData,
    ) -> None:
        """Delete existing keypair resource policy should return the deleted policy."""
        mock_repository.remove_keypair_resource_policy = AsyncMock(return_value=sample_policy_data)

        action = DeleteKeyPairResourcePolicyAction(name=sample_policy_data.name)

        result = await service.delete_keypair_resource_policy(action)

        assert result.keypair_resource_policy.name == sample_policy_data.name
        mock_repository.remove_keypair_resource_policy.assert_called_once_with(
            sample_policy_data.name
        )

    async def test_delete_nonexistent_raises_not_found(
        self,
        service: KeypairResourcePolicyService,
        mock_repository: MagicMock,
    ) -> None:
        """Delete non-existent keypair resource policy should raise KeypairResourcePolicyNotFound."""
        mock_repository.remove_keypair_resource_policy = AsyncMock(
            side_effect=KeypairResourcePolicyNotFound("Policy not found")
        )

        action = DeleteKeyPairResourcePolicyAction(name="non-existent-policy")

        with pytest.raises(KeypairResourcePolicyNotFound):
            await service.delete_keypair_resource_policy(action)
