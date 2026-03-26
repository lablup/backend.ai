"""Regression tests for ServiceHandler._run_validation.

BA-5418: _run_validation was passing request["user"]["resource_policy"] as
keypair_resource_policy, causing KeyError: 'allowed_vfolder_hosts' because
user_resource_policies table does not contain that column.
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.dto.manager.model_serving.request import (
    NewServiceRequestModel,
)
from ai.backend.common.types import AccessKey
from ai.backend.manager.api.rest.service.handler import ServiceHandler
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.auth.actions.resolve_access_key_scope import (
    ResolveAccessKeyScopeResult,
)
from ai.backend.manager.services.model_serving.actions.validate_model_service import (
    ValidateModelServiceAction,
    ValidateModelServiceActionResult,
)


def _make_request(
    keypair_resource_policy: dict[str, Any],
    user_resource_policy: dict[str, Any],
) -> dict[str, Any]:
    """Build a minimal fake aiohttp request dict for _run_validation."""
    return {
        "keypair": {
            "access_key": "TESTACCESSKEY01",
            "resource_policy": keypair_resource_policy,
        },
        "user": {
            "uuid": uuid.UUID("00000000-0000-0000-0000-000000000001"),
            "role": UserRole.USER,
            "domain_name": "default",
            "resource_policy": user_resource_policy,
        },
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
    def keypair_resource_policy(self) -> dict[str, Any]:
        """Keypair policy — contains allowed_vfolder_hosts (from keypair_resource_policies)."""
        return {
            "allowed_vfolder_hosts": {"default-nfs": "rw"},
            "max_vfolder_count": 10,
            "max_vfolder_size": 0,
            "max_quota_scope_size": -1,
        }

    @pytest.fixture
    def user_resource_policy(self) -> dict[str, Any]:
        """User policy — does NOT contain allowed_vfolder_hosts (from user_resource_policies)."""
        return {
            "max_session_count_per_model_session": 8,
        }

    @pytest.fixture
    def mock_auth(self, keypair_resource_policy: dict[str, Any]) -> MagicMock:
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
                model_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
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
        )

    async def test_keypair_resource_policy_is_used(
        self,
        handler: ServiceHandler,
        keypair_resource_policy: dict[str, Any],
        user_resource_policy: dict[str, Any],
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
        assert action.keypair_resource_policy is keypair_resource_policy
        assert "allowed_vfolder_hosts" in action.keypair_resource_policy

        # The user resource policy (without allowed_vfolder_hosts) must NOT be used.
        assert action.keypair_resource_policy is not user_resource_policy
        assert "allowed_vfolder_hosts" not in user_resource_policy

    async def test_max_session_count_from_user_resource_policy(
        self,
        handler: ServiceHandler,
        keypair_resource_policy: dict[str, Any],
        user_resource_policy: dict[str, Any],
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
