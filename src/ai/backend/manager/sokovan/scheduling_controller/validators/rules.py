"""Validator rules for session creation."""

from typing import Mapping

from ai.backend.common.exception import BackendAIError
from ai.backend.common.service_ports import parse_service_ports
from ai.backend.common.types import SlotName, SlotTypes
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.kernel import QuotaExceeded
from ai.backend.manager.models import PRIVATE_SESSION_TYPES
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    AllowedScalingGroup,
    SessionCreationContext,
    SessionCreationSpec,
)

from .base import SessionValidatorRule


class ContainerLimitRule(SessionValidatorRule):
    """Validates cluster size against resource policy limits."""

    def name(self) -> str:
        return "container_limit"

    def validate(
        self,
        spec: SessionCreationSpec,
        context: SessionCreationContext,
        allowed_groups: list[AllowedScalingGroup],
    ) -> None:
        max_containers = spec.resource_policy.get("max_containers_per_session", 1)
        if spec.cluster_size > int(max_containers):
            raise QuotaExceeded(
                f"You cannot create session with more than {max_containers} containers."
            )


class ScalingGroupAccessRule(SessionValidatorRule):
    """Validates that the scaling group is accessible."""

    def name(self) -> str:
        return "scaling_group_access"

    def validate(
        self,
        spec: SessionCreationSpec,
        context: SessionCreationContext,
        allowed_groups: list[AllowedScalingGroup],
    ) -> None:
        if not spec.scaling_group:
            # Should have been resolved already
            return

        public_sgroup_only = spec.session_type not in PRIVATE_SESSION_TYPES

        # Find the scaling group in allowed list
        for sg in allowed_groups:
            if sg.name == spec.scaling_group:
                if public_sgroup_only and sg.is_private:
                    raise InvalidAPIParameters(
                        f"Scaling group {spec.scaling_group} is not allowed for {spec.session_type} sessions"
                    )
                return

        raise InvalidAPIParameters(f"Scaling group {spec.scaling_group} is not accessible")


class ServicePortRule(SessionValidatorRule):
    """Validates preopen ports against service ports."""

    def name(self) -> str:
        return "service_port"

    def validate(
        self,
        spec: SessionCreationSpec,
        context: SessionCreationContext,
        allowed_groups: list[AllowedScalingGroup],
    ) -> None:
        # Check preopen_ports from creation_config (applies to all kernels)
        creation_preopen_ports = spec.creation_spec.get("preopen_ports")
        if creation_preopen_ports and isinstance(creation_preopen_ports, list):
            # Validate against reserved ports
            for preopen_port in creation_preopen_ports:
                if isinstance(preopen_port, int) and preopen_port in (2000, 2001, 2200, 7681):
                    raise InvalidAPIParameters(
                        "Port 2000, 2001, 2200 and 7681 are reserved for internal use"
                    )

        # Validate for each kernel spec
        for kernel_spec in spec.kernel_specs:
            # Get preopen ports from kernel spec or fall back to creation config
            preopen_ports = kernel_spec.get("preopen_ports") or creation_preopen_ports
            if not preopen_ports:
                continue
            if not isinstance(preopen_ports, list):
                continue

            # Get image info for this kernel
            image_ref = kernel_spec.get("image_ref")
            if not image_ref or not hasattr(image_ref, "canonical"):
                continue

            image_info = context.image_infos.get(image_ref.canonical)
            if not image_info:
                continue

            # Parse service ports from image labels
            service_ports = parse_service_ports(
                image_info.labels.get("ai.backend.service-ports", ""),
                image_info.labels.get("ai.backend.endpoint-ports", ""),
                BackendAIError,
            )

            for preopen_port in preopen_ports:
                # Check reserved ports (double-check in case it's from kernel spec)
                if isinstance(preopen_port, int) and preopen_port in (2000, 2001, 2200, 7681):
                    raise InvalidAPIParameters(
                        "Port 2000, 2001, 2200 and 7681 are reserved for internal use"
                    )

                # Check overlap with service ports
                for service_port in service_ports:
                    if (
                        isinstance(preopen_port, int)
                        and preopen_port in service_port["container_ports"]
                    ):
                        raise InvalidAPIParameters(
                            "Preopen port allocation cannot overlap with "
                            "service port predefined by image"
                        )


class ResourceLimitRule(SessionValidatorRule):
    """Validates requested resources against image limits."""

    def name(self) -> str:
        return "resource_limit"

    def __init__(self, known_slot_types: Mapping[SlotName, SlotTypes] | None = None):
        self._known_slot_types = known_slot_types

    def validate(
        self,
        spec: SessionCreationSpec,
        context: SessionCreationContext,
        allowed_groups: list[AllowedScalingGroup],
    ) -> None:
        # Note: This validation should ideally be done after resource calculation
        # For now, we'll validate what we can from the spec
        pass  # Resource validation is handled in ResourceCalculator for now
