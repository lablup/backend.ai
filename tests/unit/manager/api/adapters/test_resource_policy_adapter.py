from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.dto.manager.v2.common import ResourceSlotEntryInput
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    UpdateKeypairResourcePolicyInput,
)
from ai.backend.common.types import DefaultForUnspecified, ResourceSlot
from ai.backend.manager.api.adapters.resource_policy.adapter import ResourcePolicyAdapter
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.services.keypair_resource_policy.actions.modify_keypair_resource_policy import (
    ModifyKeyPairResourcePolicyActionResult,
)


class TestKeypairResourcePolicyUpdate:
    @pytest.fixture
    def policy_data(self) -> KeyPairResourcePolicyData:
        return KeyPairResourcePolicyData(
            name="default",
            created_at=None,
            default_for_unspecified=DefaultForUnspecified.LIMITED,
            total_resource_slots=ResourceSlot({"cpu": "8"}),
            max_session_lifetime=0,
            max_concurrent_sessions=30,
            max_pending_session_count=None,
            max_pending_session_resource_slots=ResourceSlot({"cpu": "4"}),
            max_concurrent_sftp_sessions=1,
            max_containers_per_session=1,
            idle_timeout=0,
            allowed_vfolder_hosts={},
        )

    @pytest.fixture
    def mock_processors(self, policy_data: KeyPairResourcePolicyData) -> MagicMock:
        processors = MagicMock()
        processors.keypair_resource_policy.modify_keypair_resource_policy.wait_for_complete = (
            AsyncMock(
                return_value=ModifyKeyPairResourcePolicyActionResult(
                    keypair_resource_policy=policy_data
                )
            )
        )
        return processors

    @pytest.fixture
    def adapter(self, mock_processors: MagicMock) -> ResourcePolicyAdapter:
        return ResourcePolicyAdapter(mock_processors)

    async def test_pending_slot_limit_is_converted_to_a_resource_slot(
        self, adapter: ResourcePolicyAdapter, mock_processors: MagicMock
    ) -> None:
        # The column is a ResourceSlotColumn and calls to_json() on whatever it
        # is handed, so a plain dict reaches the driver and raises.
        await adapter.admin_update_keypair_resource_policy(
            "default",
            UpdateKeypairResourcePolicyInput(
                max_pending_session_resource_slots=[
                    ResourceSlotEntryInput(resource_type="cpu", quantity="4")
                ]
            ),
        )

        action = mock_processors.keypair_resource_policy.modify_keypair_resource_policy.wait_for_complete.await_args.args[
            0
        ]
        applied = action.updater.spec.max_pending_session_resource_slots.value()
        assert isinstance(applied, ResourceSlot)
        assert applied == ResourceSlot({"cpu": "4"})
