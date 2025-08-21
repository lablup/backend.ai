"""Cluster configuration preparation rule."""

from typing import Any

from ai.backend.common.types import KernelEnqueueingConfig
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    SessionCreationContext,
    SessionCreationSpec,
)

from .base import SessionPreparerRule


class ClusterConfigurationRule(SessionPreparerRule):
    """Prepares cluster kernel configurations."""

    def name(self) -> str:
        return "cluster_configuration"

    def prepare(
        self,
        spec: SessionCreationSpec,
        context: SessionCreationContext,
        preparation_data: dict[str, Any],
    ) -> None:
        """Prepare cluster kernel configurations."""
        if spec.cluster_size > 1:
            kernel_configs = self._prepare_cluster_kernels(spec)
        else:
            # Single kernel session
            kernel_configs = spec.kernel_specs.copy()
            if kernel_configs and "cluster_role" not in kernel_configs[0]:
                kernel_configs[0]["cluster_role"] = DEFAULT_ROLE

        preparation_data["kernel_configs"] = kernel_configs

    def _prepare_cluster_kernels(self, spec: SessionCreationSpec) -> list[KernelEnqueueingConfig]:
        """Prepare kernel configurations for multi-container cluster."""
        if len(spec.kernel_specs) == 1:
            # Replicate the single kernel spec for all cluster nodes
            single_spec = spec.kernel_specs[0]
            kernel_configs = []

            for idx in range(spec.cluster_size):
                kernel_config = single_spec.copy()
                if idx == 0:
                    kernel_config["cluster_role"] = DEFAULT_ROLE
                else:
                    kernel_config["cluster_role"] = f"sub-{idx}"
                kernel_configs.append(kernel_config)
        else:
            # Use provided kernel specs
            kernel_configs = spec.kernel_specs.copy()

            # Ensure the first kernel is marked as main
            if kernel_configs and "cluster_role" not in kernel_configs[0]:
                kernel_configs[0]["cluster_role"] = DEFAULT_ROLE

        return kernel_configs
