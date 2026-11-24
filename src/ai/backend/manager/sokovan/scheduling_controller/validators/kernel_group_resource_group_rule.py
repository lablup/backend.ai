"""Validator for the resource groups the kernel groups of one session name."""

from __future__ import annotations

from typing import override

from ai.backend.common.types import ClusterMode
from ai.backend.manager.data.session.spec import SessionSpec
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.sokovan.scheduling_controller.validators.session_spec_base import (
    SessionSpecValidatorRule,
)
from ai.backend.manager.views.sokovan.session_creation import (
    ResourceGroupEnqueueInfo,
    SessionSpecContext,
)


class KernelGroupResourceGroupRule(SessionSpecValidatorRule):
    """Kernels of one session share an agent in single-node mode and one network type."""

    @override
    def name(self) -> str:
        return "kernel_group_resource_group"

    @override
    def validate(
        self,
        spec: SessionSpec,
        context: SessionSpecContext,
    ) -> None:
        options = spec.resource_spec.options
        resource_groups = [
            context.resource_group_of_role(group.role) for group in options.kernel_groups
        ]
        names = sorted({str(resource_group.name) for resource_group in resource_groups})
        if len(names) <= 1:
            return
        if options.cluster_mode == ClusterMode.SINGLE_NODE:
            raise InvalidAPIParameters(
                extra_msg=(
                    f"a single-node session cannot have kernel groups in different "
                    f"resource groups {names}. Use the multi-node cluster mode."
                ),
            )
        if len({self._uses_host_network(group) for group in resource_groups}) > 1:
            raise InvalidAPIParameters(
                extra_msg=(
                    f"resource groups {names} differ in the use of the host network, "
                    f"so their kernels cannot share a session."
                ),
            )

    def _uses_host_network(self, resource_group: ResourceGroupEnqueueInfo) -> bool:
        return resource_group.network is not None and resource_group.network.use_host_network
