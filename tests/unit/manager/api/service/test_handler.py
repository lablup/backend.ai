"""Regression tests for ServiceHandler._run_validation.

BA-5418: _run_validation was passing request["user"]["resource_policy"] as
keypair_resource_policy, causing KeyError: 'allowed_vfolder_hosts' because
user_resource_policies table does not contain that column.
"""

from __future__ import annotations

import dataclasses
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.dto.manager.model_serving.request import (
    NewServiceRequestModel,
)
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.user import UserID
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.common.types import AccessKey, DefaultForUnspecified, ResourceSlot
from ai.backend.manager.api.rest.service.handler import ServiceHandler
from ai.backend.manager.data.auth.types import AuthenticatedKeypair, AuthenticatedUser
from ai.backend.manager.data.resource.types import (
    KeyPairResourcePolicyData,
    UserResourcePolicyData,
)
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.auth.actions.resolve_access_key_scope import (
    ResolveAccessKeyScopeResult,
)
from ai.backend.manager.services.model_serving.actions.validate_model_service import (
    ValidateModelServiceAction,
    ValidateModelServiceActionResult,
)


def _make_request(
    keypair_resource_policy: KeyPairResourcePolicyData,
    user_resource_policy: UserResourcePolicyData,
) -> dict[str, Any]:
    """Build a minimal fake aiohttp request dict for _run_validation."""
    return {
        "keypair": AuthenticatedKeypair(
            access_key=AccessKey("TESTACCESSKEY01"),
            secret_key=None,
            is_admin=False,
            rate_limit=None,
            resource_policy=keypair_resource_policy,
        ),
        "user": AuthenticatedUser(
            uuid=UserID(uuid.UUID("00000000-0000-0000-0000-000000000001")),
            email="test@example.com",
            role=UserRole.USER,
            domain_name="default",
            domain_id=DomainID(uuid.uuid4()),
            sudo_session_enabled=False,
            main_access_key=None,
            allowed_client_ip=None,
            resource_policy=user_resource_policy,
        ),
    }


def _make_params() -> NewServiceRequestModel:
    return NewServiceRequestModel.model_validate({
        "name": "test-model-svc",
        "desired_session_count": 1,
        "config": {
            "model": "my-model",
            "scalingGroup": "default",
        },
    })


class TestRunValidationUsesKeypairResourcePolicy:
    """Regression tests for BA-5418: _run_validation must use keypair resource policy."""

    @pytest.fixture
    def keypair_resource_policy(self) -> KeyPairResourcePolicyData:
        """Keypair policy — carries allowed_vfolder_hosts (from keypair_resource_policies)."""
        return KeyPairResourcePolicyData(
            name="default",
            created_at=None,
            default_for_unspecified=DefaultForUnspecified.LIMITED,
            total_resource_slots=ResourceSlot(),
            max_session_lifetime=0,
            max_concurrent_sessions=10,
            max_pending_session_count=None,
            max_pending_session_resource_slots=None,
            max_priority=None,
            max_concurrent_sftp_sessions=2,
            max_containers_per_session=1,
            idle_timeout=3600,
            allowed_vfolder_hosts={"default-nfs": "rw"},
        )

    @pytest.fixture
    def user_resource_policy(self) -> UserResourcePolicyData:
        """User policy — has no allowed_vfolder_hosts (from user_resource_policies)."""
        return UserResourcePolicyData(
            name="default",
            max_session_count_per_model_session=8,
        )

    @pytest.fixture
    def mock_auth(self, keypair_resource_policy: KeyPairResourcePolicyData) -> MagicMock:
        scope_result = ResolveAccessKeyScopeResult(
            requester_access_key=AccessKey("TESTACCESSKEY01"),
            owner_access_key=AccessKey("TESTACCESSKEY01"),
        )
        mock = MagicMock()
        mock.resolve_access_key_scope = MagicMock()
        mock.resolve_access_key_scope.wait_for_complete = AsyncMock(return_value=scope_result)
        return mock

    @pytest.fixture
    def captured_validate_action(self) -> list[ValidateModelServiceAction]:
        return []

    @pytest.fixture
    def mock_model_serving(
        self,
        captured_validate_action: list[ValidateModelServiceAction],
    ) -> MagicMock:
        async def _capture(action: ValidateModelServiceAction) -> ValidateModelServiceActionResult:
            captured_validate_action.append(action)
            return ValidateModelServiceActionResult(
                model_vfolder_id=VFolderUUID(
                    uuid.UUID("11111111-1111-1111-1111-111111111111"),
                ),
                model_definition_path=None,
                requester_access_key=action.requester_access_key,
                owner_access_key=action.owner_access_key,
                owner_uuid=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                owner_role=UserRole.USER,
                group_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
                resource_policy=action.keypair_resource_policy,
                scaling_group="default",
                extra_mounts=[],
            )

        mock = MagicMock()
        mock.validate_model_service = MagicMock()
        mock.validate_model_service.wait_for_complete = AsyncMock(side_effect=_capture)
        return mock

    @pytest.fixture
    def handler(self, mock_auth: MagicMock, mock_model_serving: MagicMock) -> ServiceHandler:
        return ServiceHandler(
            auth=mock_auth,
            deployment=MagicMock(),
            model_serving=mock_model_serving,
            model_serving_auto_scaling=MagicMock(),
            runtime_variant=MagicMock(),
        )

    async def test_keypair_resource_policy_is_used(
        self,
        handler: ServiceHandler,
        keypair_resource_policy: KeyPairResourcePolicyData,
        user_resource_policy: UserResourcePolicyData,
        captured_validate_action: list[ValidateModelServiceAction],
    ) -> None:
        """ValidateModelServiceAction must use keypair resource policy, not user resource policy.

        Regression test for BA-5418: using user resource policy caused
        KeyError: 'allowed_vfolder_hosts' when model service had extra vfolder mounts.
        """
        request = _make_request(keypair_resource_policy, user_resource_policy)
        params = _make_params()

        await handler._run_validation(request, params)

        assert len(captured_validate_action) == 1
        action = captured_validate_action[0]

        # The keypair resource policy (with allowed_vfolder_hosts) must be used.
        assert action.keypair_resource_policy == dataclasses.asdict(keypair_resource_policy)
        assert "allowed_vfolder_hosts" in action.keypair_resource_policy

        # The user resource policy (without allowed_vfolder_hosts) must NOT be used.
        assert action.keypair_resource_policy != dataclasses.asdict(user_resource_policy)

    async def test_max_session_count_from_user_resource_policy(
        self,
        handler: ServiceHandler,
        keypair_resource_policy: KeyPairResourcePolicyData,
        user_resource_policy: UserResourcePolicyData,
        captured_validate_action: list[ValidateModelServiceAction],
    ) -> None:
        """max_session_count_per_model_session must still come from user resource policy.

        Verifies that the fix for BA-5418 did not break the correct sourcing of
        max_session_count_per_model_session from request["user"]["resource_policy"].
        """
        request = _make_request(keypair_resource_policy, user_resource_policy)
        params = _make_params()

        await handler._run_validation(request, params)

        assert len(captured_validate_action) == 1
        action = captured_validate_action[0]
        assert action.max_session_count_per_model_session == 8
