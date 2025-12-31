from __future__ import annotations

from unittest.mock import Mock

from graphql import Undefined

from ai.backend.manager.models.resource_policy import ModifyKeyPairResourcePolicyInput
from ai.backend.manager.types import _TriStateEnum


class TestModifyKeyPairResourcePolicyInputType:
    def test_empty_total_resource_slots_should_be_updated(self) -> None:
        """
        Regression test: empty dict {} for total_resource_slots should result in UPDATE state.

        Previously, empty dict was treated as falsy and converted to Undefined,
        causing the field to be skipped during updates.
        """
        mock_input = Mock(spec=ModifyKeyPairResourcePolicyInput)
        mock_input.total_resource_slots = {}
        mock_input.default_for_unspecified = Undefined
        mock_input.max_session_lifetime = Undefined
        mock_input.max_concurrent_sessions = Undefined
        mock_input.max_concurrent_sftp_sessions = Undefined
        mock_input.max_containers_per_session = Undefined
        mock_input.idle_timeout = Undefined
        mock_input.allowed_vfolder_hosts = Undefined
        mock_input.max_vfolder_count = Undefined
        mock_input.max_vfolder_size = Undefined
        mock_input.max_quota_scope_size = Undefined
        mock_input.max_pending_session_count = Undefined
        mock_input.max_pending_session_resource_slots = Undefined

        result = ModifyKeyPairResourcePolicyInput.to_updater(mock_input, "test_policy")
        assert result.spec.total_resource_slots._state == _TriStateEnum.UPDATE  # type: ignore[attr-defined]
