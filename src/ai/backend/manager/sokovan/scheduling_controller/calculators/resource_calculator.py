"""Stateless calculator for resource requirements."""

import logging
from decimal import Decimal
from typing import Any, Mapping, Optional

from ai.backend.common.types import (
    BinarySize,
    ResourceSlot,
    SlotName,
    SlotTypes,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.defs import DEFAULT_SHARED_MEMORY_SIZE, INTRINSIC_SLOTS
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    AllowedScalingGroup,
    ImageInfo,
    ScalingGroupNetworkInfo,
    SessionCreationContext,
    SessionCreationSpec,
)

from ..types import CalculatedResources, KernelResourceInfo

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ResourceCalculator:
    """Stateless calculator for resource requirements."""

    def __init__(self, config_provider: ManagerConfigProvider):
        self._config_provider = config_provider

    async def calculate(
        self,
        validated_scaling_group: AllowedScalingGroup,
        spec: SessionCreationSpec,
        context: SessionCreationContext,
    ) -> CalculatedResources:
        """
        Calculate all resources for the session.

        Args:
            validated_scaling_group: Validated scaling group
            spec: Session creation specification
            context: Session creation context with fetched data

        Returns:
            CalculatedResources with pre-calculated resource information
        """
        kernel_resources: list[KernelResourceInfo] = []
        session_requested_slots = ResourceSlot()

        # Determine the actual number of kernels that will be created
        # For multi-node sessions with a single kernel spec, we replicate it for all nodes
        kernel_specs_to_calculate = []
        if spec.cluster_size > 1 and len(spec.kernel_specs) == 1:
            # Multi-node session with single spec - will be replicated for each node
            log.debug("Multi-node session: replicating single spec for {} nodes", spec.cluster_size)
            for _ in range(spec.cluster_size):
                kernel_specs_to_calculate.append(spec.kernel_specs[0])
        else:
            # Single node or multi-spec multi-node - use specs as-is
            kernel_specs_to_calculate = spec.kernel_specs

        log.debug(
            "Resource calculation: cluster_size={}, original_specs={}, calculating_for={} kernels",
            spec.cluster_size,
            len(spec.kernel_specs),
            len(kernel_specs_to_calculate),
        )

        # Calculate resources for each kernel
        for kernel_spec in kernel_specs_to_calculate:
            # Get image info for this kernel
            image_ref = kernel_spec.get("image_ref")
            if not image_ref:
                continue

            # Image info must exist at this point (already checked before)
            image_info = context.image_infos[image_ref.canonical]

            # Calculate kernel resources
            requested_slots, resource_opts = await self.calculate_kernel_resources(
                validated_scaling_group,
                spec.creation_spec,
                image_info,
                context.scaling_group_network,
            )

            kernel_resources.append(
                KernelResourceInfo(
                    requested_slots=requested_slots,
                    resource_opts=resource_opts,
                )
            )

            # Accumulate for session total
            session_requested_slots += requested_slots

        log.debug(
            "Resource calculation complete: calculated resources for {} kernels, total slots={}",
            len(kernel_resources),
            session_requested_slots,
        )

        return CalculatedResources(
            session_requested_slots=session_requested_slots,
            kernel_resources=kernel_resources,
        )

    async def calculate_kernel_resources(
        self,
        validated_scaling_group: AllowedScalingGroup,
        creation_config: dict,
        image_info: ImageInfo,
        scaling_group_network: ScalingGroupNetworkInfo,
    ) -> tuple[ResourceSlot, dict]:
        """
        Calculate resource requirements for a kernel.

        Args:
            kernel_spec: Kernel specification
            creation_config: Creation configuration
            image_info: Image information object
            scaling_group_network: Scaling group network configuration

        Returns:
            tuple: (requested_slots, resource_opts)
        """
        # Get known slot types
        known_slot_types = (
            await self._config_provider.legacy_etcd_config_loader.get_resource_slots()
        )

        # Parse image resource spec to get slot ranges
        image_resource_spec = image_info.resource_spec
        image_min_slots = ResourceSlot()
        image_max_slots = ResourceSlot()

        # Parse min/max from resource spec with proper type conversion
        for slot_name, slot_spec in image_resource_spec.items():
            slot_name_typed = SlotName(slot_name)
            if slot_name_typed in known_slot_types:
                slot_unit = known_slot_types.get(slot_name_typed)

                # Process min value
                if "min" in slot_spec:
                    min_value = slot_spec["min"]
                    if min_value is None:
                        min_value = Decimal(0)
                    elif slot_unit == "bytes":
                        if not isinstance(min_value, Decimal):
                            min_value = BinarySize.from_str(str(min_value))
                    else:
                        if not isinstance(min_value, Decimal):
                            min_value = Decimal(str(min_value))
                    image_min_slots[slot_name_typed] = min_value

                # Process max value
                if "max" in slot_spec:
                    max_value = slot_spec["max"]
                    if max_value is None:
                        max_value = Decimal("Infinity")
                    elif slot_unit == "bytes":
                        if not isinstance(max_value, Decimal):
                            max_value = BinarySize.from_str(str(max_value))
                    else:
                        if not isinstance(max_value, Decimal):
                            max_value = Decimal(str(max_value))
                    image_max_slots[slot_name_typed] = max_value

        # Get resource options
        resource_opts = creation_config.get("resource_opts") or {}

        # Calculate shared memory
        resource_opts = await self._apply_shared_memory_adjustments(
            validated_scaling_group,
            resource_opts,
            image_info.labels,
            image_min_slots,
        )

        # Calculate requested slots
        requested_slots = await self._calculate_requested_slots(
            creation_config,
            image_min_slots,
            known_slot_types,
        )

        # Validate requested slots against image limits
        self._validate_resource_limits(
            requested_slots,
            image_min_slots,
            image_max_slots,
            resource_opts.get("shmem"),
            known_slot_types,
        )

        return requested_slots, resource_opts

    async def _calculate_requested_slots(
        self,
        creation_config: dict,
        image_min_slots: ResourceSlot,
        known_slot_types: Mapping[SlotName, SlotTypes],
    ) -> ResourceSlot:
        """Calculate requested resource slots from creation config."""
        if (resources := creation_config.get("resources")) is not None:
            # Modern client with explicit resource specification
            return await self._calculate_from_resources(
                resources,
                image_min_slots,
                known_slot_types,
            )
        else:
            # Legacy client support (prior to v19.03)
            return await self._calculate_from_legacy(
                creation_config,
                image_min_slots,
                known_slot_types,
            )

    async def _calculate_from_resources(
        self,
        resources: dict,
        image_min_slots: ResourceSlot,
        known_slot_types: Mapping[SlotName, SlotTypes],
    ) -> ResourceSlot:
        """Calculate slots from modern resource specification."""
        # Validate unknown slot types
        for slot_key, slot_value in resources.items():
            if slot_value != 0 and slot_key not in known_slot_types:
                raise InvalidAPIParameters(f"Unknown requested resource slot: {slot_key}")

        try:
            requested_slots = ResourceSlot.from_user_input(resources, known_slot_types)
        except ValueError:
            log.exception("request_slots & image_slots calculation error")
            raise InvalidAPIParameters(
                "Your resource request has resource type(s) not supported by the image."
            )

        # Fill intrinsic resources with image minimums if not specified
        for k, v in requested_slots.items():
            if (v is None or v == 0) and k in INTRINSIC_SLOTS:
                requested_slots[k] = image_min_slots[k]

        return requested_slots

    async def _calculate_from_legacy(
        self,
        creation_config: dict,
        image_min_slots: ResourceSlot,
        known_slot_types: Mapping[SlotName, SlotTypes],
    ) -> ResourceSlot:
        """Calculate slots from legacy client format."""
        cpu = creation_config.get("instanceCores")
        if cpu is None:
            cpu = image_min_slots["cpu"]

        mem = creation_config.get("instanceMemory")
        if mem is None:
            mem = image_min_slots["mem"]
        else:
            # In legacy clients, memory is normalized to GiB
            mem = str(mem) + "g"

        requested_slots = ResourceSlot.from_user_input(
            {"cpu": cpu, "mem": mem},
            known_slot_types,
        )

        # Check for unsupported accelerators in legacy format
        if creation_config.get("instanceGPUs") is not None:
            raise InvalidAPIParameters("Client upgrade required to use GPUs (v19.03+).")
        if creation_config.get("instanceTPUs") is not None:
            raise InvalidAPIParameters("Client upgrade required to use TPUs (v19.03+).")

        return requested_slots

    async def _apply_shared_memory_adjustments(
        self,
        validated_scaling_group: AllowedScalingGroup,
        resource_opts: dict[str, Any],
        image_labels: dict,
        image_min_slots: ResourceSlot,
    ) -> dict:
        """Apply shared memory adjustments to resource options."""
        resource_opts = resource_opts.copy()

        # Get shared memory size
        raw_shmem: Optional[str] = resource_opts.get("shmem")
        if raw_shmem is None:
            raw_shmem = image_labels.get("ai.backend.resource.preferred.shmem")
        if not raw_shmem:
            raw_shmem = DEFAULT_SHARED_MEMORY_SIZE

        try:
            shmem = BinarySize.from_str(raw_shmem)
        except ValueError:
            log.warning(
                f"Failed to convert raw `shmem({raw_shmem})` "
                f"to a decimal value. Fallback to default({DEFAULT_SHARED_MEMORY_SIZE})."
            )
            shmem = BinarySize.from_str(DEFAULT_SHARED_MEMORY_SIZE)

        resource_opts["shmem"] = shmem

        allow_fractional = resource_opts.get("allow_fractional_resource_fragmentation")
        if allow_fractional is None:
            allow_fractional = (
                validated_scaling_group.scheduler_opts.allow_fractional_resource_fragmentation
            )

        resource_opts["allow_fractional_resource_fragmentation"] = allow_fractional

        # Adjust image minimum slots for shared memory
        image_min_slots["mem"] += shmem

        return resource_opts

    def _validate_resource_limits(
        self,
        requested_slots: ResourceSlot,
        image_min_slots: ResourceSlot,
        image_max_slots: ResourceSlot,
        shmem: Optional[BinarySize],
        known_slot_types: Mapping[SlotName, SlotTypes],
    ) -> None:
        """Validate requested resources against image limits."""
        # Check if: requested >= image-minimum
        if image_min_slots > requested_slots:
            min_humanized = " ".join(
                f"{k}={v}" for k, v in image_min_slots.to_humanized(known_slot_types).items()
            )
            raise InvalidAPIParameters(
                f"Your resource request is smaller than the minimum required by the image. ({min_humanized})"
            )

        # Check if: shmem < memory
        if shmem and shmem >= requested_slots["mem"]:
            raise InvalidAPIParameters(
                f"Shared memory should be less than the main memory. (s:{shmem}, m:{BinarySize(requested_slots['mem'])})"
            )
