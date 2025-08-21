"""Cluster configuration validation rule."""

from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    AllowedScalingGroup,
    SessionCreationContext,
    SessionCreationSpec,
)

from .base import SessionValidatorRule


class ClusterValidationRule(SessionValidatorRule):
    """Validates cluster configuration for multi-container sessions."""

    def name(self) -> str:
        return "cluster_validation"

    def validate(
        self,
        spec: SessionCreationSpec,
        context: SessionCreationContext,
        allowed_groups: list[AllowedScalingGroup],
    ) -> None:
        """Validate cluster configuration and kernel specifications."""
        # Check if kernel_specs exists
        if not spec.kernel_specs:
            raise InvalidAPIParameters("At least one kernel specification is required")

        # Only validate multi-container sessions further
        if spec.cluster_size <= 1:
            return

        kernel_specs_count = len(spec.kernel_specs)

        if kernel_specs_count == 1:
            # Single kernel spec will be replicated - this is valid
            # The main kernel config will be replicated to sub-containers
            pass
        elif kernel_specs_count > 1:
            # Each container should have its own kernel_config
            if kernel_specs_count != spec.cluster_size:
                raise InvalidAPIParameters(
                    "The number of kernel configs differs from the cluster size"
                )
