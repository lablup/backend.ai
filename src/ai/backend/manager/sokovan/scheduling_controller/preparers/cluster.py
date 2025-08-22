"""Cluster configuration preparation rule."""

from typing import Any, cast

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
            main_kernel_config = spec.kernel_specs[0].copy()
            kernel_configs = []

            # Configure main kernel (cluster_idx = 1)
            main_kernel_config["cluster_role"] = "main"
            main_kernel_config["cluster_idx"] = 1
            main_kernel_config["local_rank"] = 0
            main_kernel_config["cluster_hostname"] = "main1"
            kernel_configs.append(main_kernel_config)

            # Configure sub kernels (cluster_idx starts from 1 for sub1, 2 for sub2, etc.)
            for i in range(spec.cluster_size - 1):
                sub_kernel_config = cast(KernelEnqueueingConfig, {**main_kernel_config})
                sub_kernel_config["cluster_role"] = "sub"
                sub_kernel_config["cluster_idx"] = i + 1  # sub1: 1, sub2: 2, ...
                sub_kernel_config["local_rank"] = i + 1  # sub1: 1, sub2: 2, ...
                sub_kernel_config["cluster_hostname"] = f"sub{i + 1}"
                kernel_configs.append(sub_kernel_config)
        else:
            # Use provided kernel specs - each container has its own config
            kernel_configs = []
            for idx, kernel_spec in enumerate(spec.kernel_specs):
                kernel_config = kernel_spec.copy()

                # Check if cluster_role is already defined
                if "cluster_role" not in kernel_config:
                    # Assign default roles based on position
                    if idx == 0:
                        kernel_config["cluster_role"] = DEFAULT_ROLE
                    else:
                        kernel_config["cluster_role"] = "sub"

                # Set cluster_idx if not already set
                if "cluster_idx" not in kernel_config:
                    if kernel_config["cluster_role"] == DEFAULT_ROLE:
                        kernel_config["cluster_idx"] = 1
                    else:
                        # For sub kernels, find the count of previous sub kernels
                        sub_count = sum(
                            1 for i in range(idx) if kernel_configs[i].get("cluster_role") == "sub"
                        )
                        kernel_config["cluster_idx"] = sub_count + 1

                # Set local_rank if not already set
                if "local_rank" not in kernel_config:
                    kernel_config["local_rank"] = idx

                # Set cluster_hostname if not already set
                if "cluster_hostname" not in kernel_config:
                    role = kernel_config["cluster_role"]
                    idx_val = kernel_config["cluster_idx"]
                    kernel_config["cluster_hostname"] = f"{role}{idx_val}"

                kernel_configs.append(kernel_config)

        return kernel_configs
