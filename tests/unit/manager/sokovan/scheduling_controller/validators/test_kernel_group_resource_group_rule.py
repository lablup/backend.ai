"""Tests for the resource groups the kernel groups of one session may name."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass

import pytest

from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.resource_group import ResourceGroupID, ResourceGroupName
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.types import AccessKey, ClusterMode, SessionTypes
from ai.backend.manager.data.dotfile.types import DotfileBundle
from ai.backend.manager.data.network.types import NetworkType
from ai.backend.manager.data.resource.types import SlotTypeInfo
from ai.backend.manager.data.session.creation import ContainerUserInfo, ResourceGroupNetworkInfo
from ai.backend.manager.data.session.options import (
    DefaultSessionOptions,
    KernelExecutionSpec,
    KernelGroup,
    KernelResourceConfig,
    SchedulingTarget,
    SessionHandlerOptions,
    SessionOptions,
)
from ai.backend.manager.data.session.spec import (
    SessionClassification,
    SessionIdentity,
    SessionNetwork,
    SessionResourceSpec,
    SessionScope,
    SessionSpec,
)
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.sokovan.scheduling_controller.validators.kernel_group_resource_group_rule import (
    KernelGroupResourceGroupRule,
)
from ai.backend.manager.views.sokovan.session_creation import (
    GlobalEnqueueInfo,
    ResourceGroupEnqueueInfo,
    SessionSpecContext,
    UserEnqueueInfo,
)


def _resource_group(name: str, *, use_host_network: bool = False) -> ResourceGroupEnqueueInfo:
    return ResourceGroupEnqueueInfo(
        name=ResourceGroupName(name),
        defaults=DefaultSessionOptions(),
        network=ResourceGroupNetworkInfo(use_host_network=use_host_network),
        allow_fractional=False,
        served_slot_names=frozenset(),
    )


def _spec(cluster_mode: ClusterMode) -> SessionSpec:
    """A session of the ``npu`` group with a main and a gpu kernel group."""
    execution_spec = KernelExecutionSpec(
        resource_input=KernelResourceConfig(image_id=ImageID(uuid.uuid4()), resources=[])
    )
    return SessionSpec(
        resource_spec=SessionResourceSpec(
            identity=SessionIdentity(
                session_id=SessionID(uuid.uuid4()),
                creation_id="c-1",
                session_name="s",
                access_key=AccessKey("AK"),
                user_uuid=uuid.uuid4(),
            ),
            classification=SessionClassification(session_type=SessionTypes.INTERACTIVE),
            network=SessionNetwork(network_type=NetworkType.VOLATILE),
            options=SessionOptions(
                priority=10,
                is_preemptible=True,
                cluster_mode=cluster_mode,
                cluster_size=2,
                scheduling_target=SchedulingTarget(),
                kernel_groups=[
                    KernelGroup(role=role, replica_count=1, execution_spec=execution_spec)
                    for role in ("main", "gpu")
                ],
                handler_options=SessionHandlerOptions(),
            ),
            kernel_specs=(),
        ),
        scope=SessionScope(
            domain_id=DomainID(uuid.uuid4()),
            domain_name=DomainName("default"),
            project_id=ProjectID(uuid.uuid4()),
            resource_group_id=ResourceGroupID(uuid.uuid4()),
            resource_group_name=ResourceGroupName("npu"),
        ),
    )


def _context(
    named_resource_group_by_role: Mapping[str, ResourceGroupEnqueueInfo],
) -> SessionSpecContext:
    return SessionSpecContext(
        resource_group=_resource_group("npu"),
        user=UserEnqueueInfo(
            policy=None,
            container_user=ContainerUserInfo(),
            dotfiles=DotfileBundle(),
            default_bootstrap_script=None,
            pending_session_count=0,
            pending_session_resource_slots={},
            vfolder_mounts_by_role={},
        ),
        global_info=GlobalEnqueueInfo(
            image_infos={}, slot_type_info=SlotTypeInfo(types={}, required=frozenset())
        ),
        named_resource_group_by_role=named_resource_group_by_role,
    )


@dataclass(frozen=True)
class _KernelGroupResourceGroupCase:
    description: str
    cluster_mode: ClusterMode
    gpu_role_resource_group: ResourceGroupEnqueueInfo


class TestKernelGroupResourceGroupRule:
    @pytest.mark.parametrize(
        "case",
        [
            _KernelGroupResourceGroupCase(
                description="multi-node-in-two-groups",
                cluster_mode=ClusterMode.MULTI_NODE,
                gpu_role_resource_group=_resource_group("gpu"),
            ),
            _KernelGroupResourceGroupCase(
                description="single-node-naming-the-session-group",
                cluster_mode=ClusterMode.SINGLE_NODE,
                gpu_role_resource_group=_resource_group("npu"),
            ),
        ],
        ids=lambda case: case.description,
    )
    def test_accepts(self, case: _KernelGroupResourceGroupCase) -> None:
        KernelGroupResourceGroupRule().validate(
            _spec(case.cluster_mode), _context({"gpu": case.gpu_role_resource_group})
        )

    @pytest.mark.parametrize(
        "case",
        [
            _KernelGroupResourceGroupCase(
                description="single-node-in-two-groups",
                cluster_mode=ClusterMode.SINGLE_NODE,
                gpu_role_resource_group=_resource_group("gpu"),
            ),
            _KernelGroupResourceGroupCase(
                description="multi-node-with-one-host-network-group",
                cluster_mode=ClusterMode.MULTI_NODE,
                gpu_role_resource_group=_resource_group("gpu", use_host_network=True),
            ),
        ],
        ids=lambda case: case.description,
    )
    def test_rejects(self, case: _KernelGroupResourceGroupCase) -> None:
        with pytest.raises(InvalidAPIParameters):
            KernelGroupResourceGroupRule().validate(
                _spec(case.cluster_mode), _context({"gpu": case.gpu_role_resource_group})
            )
