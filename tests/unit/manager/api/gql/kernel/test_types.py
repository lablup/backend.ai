"""Unit tests for kernel GraphQL types."""

from __future__ import annotations

from uuid import uuid4

from ai.backend.common.dto.manager.v2.common import ResourceSlotInfo
from ai.backend.common.dto.manager.v2.kernel.response import (
    KernelAttachedDeviceInfo,
    KernelClusterInfoGQLDTO,
    KernelLifecycleInfoGQLDTO,
    KernelNetworkInfoGQLDTO,
    KernelNode,
    KernelResourceInfoGQLDTO,
    KernelSessionInfoGQLDTO,
    KernelUserInfoGQLDTO,
    ResourceAllocationGQLDTO,
)
from ai.backend.manager.api.gql.kernel.types import KernelV2AttachedDeviceGQL, KernelV2GQL


def _kernel_node(attached_devices: list[KernelAttachedDeviceInfo]) -> KernelNode:
    kernel_id = uuid4()
    return KernelNode(
        id=kernel_id,
        field_id=kernel_id,
        session_info=KernelSessionInfoGQLDTO(session_id=uuid4(), session_type="interactive"),
        user_info=KernelUserInfoGQLDTO(),
        network=KernelNetworkInfoGQLDTO(),
        cluster=KernelClusterInfoGQLDTO(
            cluster_role="main", cluster_idx=0, local_rank=0, cluster_hostname="main"
        ),
        resource=KernelResourceInfoGQLDTO(
            agent_id="agent-001",
            resource_group_name="default",
            allocation=ResourceAllocationGQLDTO(requested=ResourceSlotInfo(entries=[])),
            shares=ResourceSlotInfo(entries=[]),
            attached_devices=attached_devices,
        ),
        lifecycle=KernelLifecycleInfoGQLDTO(status="RUNNING", result="UNDEFINED"),
    )


class TestKernelV2GQLAttachedDevices:
    def test_attached_devices_convert_to_the_device_type(self) -> None:
        device = KernelAttachedDeviceInfo(
            device_name="cuda", device_id="0", model_name="NVIDIA A100"
        )

        gql = KernelV2GQL.from_pydantic(_kernel_node([device]))

        (converted,) = gql.resource.attached_devices
        assert isinstance(converted, KernelV2AttachedDeviceGQL)
        assert converted.device_name == "cuda"
        assert converted.device_id == "0"
        assert converted.model_name == "NVIDIA A100"

    def test_no_attached_device_converts_to_an_empty_list(self) -> None:
        gql = KernelV2GQL.from_pydantic(_kernel_node([]))

        assert gql.resource.attached_devices == []
