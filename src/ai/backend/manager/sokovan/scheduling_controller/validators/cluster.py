"""Cluster configuration validation rule."""

from ai.backend.common.types import KernelEnqueueingConfig
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    AllowedScalingGroup,
    SessionCreationContext,
    SessionCreationSpec,
)

from .base import SessionValidatorRule

DEFAULT_ROLE = "main"


class ClusterValidationRule(SessionValidatorRule):
    """Validates cluster configuration for multi-kernel sessions."""

    def name(self) -> str:
        return "cluster_validation"

    def validate(
        self,
        spec: SessionCreationSpec,
        context: SessionCreationContext,
        allowed_groups: list[AllowedScalingGroup],
    ) -> None:
        """Validate cluster configuration if cluster size > 1."""
        if spec.cluster_size > 1:
            kernel_configs = spec.kernel_specs
            self._validate_cluster_config(kernel_configs, spec.cluster_size)

    def _validate_cluster_config(
        self, kernel_configs: list[KernelEnqueueingConfig], cluster_size: int
    ) -> None:
        """Validate cluster configuration."""
        if len(kernel_configs) != cluster_size:
            raise InvalidAPIParameters(
                f"Kernel config count ({len(kernel_configs)}) does not match cluster size ({cluster_size})"
            )

        # Ensure exactly one main role
        main_count = sum(1 for k in kernel_configs if k.get("cluster_role") == DEFAULT_ROLE)
        if main_count != 1:
            raise InvalidAPIParameters(
                f"Cluster must have exactly one main node, found {main_count}"
            )
