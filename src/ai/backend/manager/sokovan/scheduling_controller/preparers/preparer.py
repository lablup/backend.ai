"""Session preparer that applies multiple preparation rules."""

import logging
import uuid
from collections.abc import Iterable
from datetime import datetime
from typing import Any, Optional

from dateutil.tz import tzutc

from ai.backend.common.types import (
    KernelEnqueueingConfig,
    KernelId,
    ResourceSlot,
    SessionId,
    VFolderMount,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.models.network import NetworkType
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    AllowedScalingGroup,
    KernelEnqueueData,
    SessionCreationContext,
    SessionCreationSpec,
    SessionEnqueueData,
)

from ..types import CalculatedResources
from .base import SessionPreparerRule

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class SessionPreparer:
    """
    Preparer that applies multiple preparation rules for session creation.
    """

    _rules: Iterable[SessionPreparerRule]

    # Default values for missing data
    DEFAULT_IMAGE_NAME = "ai.backend.undefined"
    DEFAULT_ARCHITECTURE = "x86_64"
    DEFAULT_REGISTRY = "localhost"

    def __init__(self, rules: Iterable[SessionPreparerRule]) -> None:
        self._rules = rules

    async def prepare(
        self,
        spec: SessionCreationSpec,
        validated_scaling_group: AllowedScalingGroup,
        context: SessionCreationContext,
        calculated_resources: CalculatedResources,
    ) -> SessionEnqueueData:
        """
        Convert creation spec to enqueue data.

        Args:
            spec: Session creation specification
            validated_scaling_group: Validated scaling group
            context: Pre-fetched context with all required data
            calculated_resources: Pre-calculated resource information

        Returns:
            Complete SessionEnqueueData with kernels and dependencies
        """
        # Initialize preparation data
        preparation_data: dict[str, Any] = {
            "dotfile_data": context.dotfile_data,
            "vfolder_mounts": context.vfolder_mounts,
        }

        # Apply all preparation rules
        for rule in self._rules:
            log.debug(f"Applying preparation rule: {rule.name()}")
            rule.prepare(spec, context, preparation_data)

        # Generate session ID if not provided
        session_id = SessionId(uuid.uuid4())

        # Use network info from context
        scaling_group_network = context.scaling_group_network

        # Prepare environment variables
        environ = dict(spec.creation_spec.get("environ") or {})

        # Add SUDO_SESSION_ENABLED to environ if sudo session is enabled
        if spec.sudo_session_enabled:
            environ["SUDO_SESSION_ENABLED"] = "1"

        # Determine network configuration
        network_type, network_id = self._determine_network_config(spec, context)

        # Extract bootstrap script and timeout
        bootstrap_script = spec.creation_spec.get("bootstrap_script")
        timeout = spec.creation_spec.get("session_timeout")

        # Build kernel data using kernel_configs from preparation_data
        kernel_configs = preparation_data.get("kernel_configs", spec.kernel_specs)
        internal_data = preparation_data.get("internal_data", {})

        kernel_data_list = await self._prepare_kernels(
            spec,
            session_id,
            validated_scaling_group,
            kernel_configs,
            internal_data,
            context.vfolder_mounts,
            context,
            calculated_resources,
        )

        # Collect images from kernels
        session_images = self._collect_session_images(kernel_data_list)

        # Use pre-calculated session total
        total_requested = calculated_resources.session_requested_slots

        # Build complete session data with all information
        session_data = SessionEnqueueData(
            id=session_id,
            creation_id=spec.session_creation_id,
            name=spec.session_name,
            access_key=spec.access_key,
            user_uuid=spec.user_scope.user_uuid,
            group_id=spec.user_scope.group_id,
            domain_name=spec.user_scope.domain_name,
            scaling_group_name=validated_scaling_group.name,
            session_type=spec.session_type,
            cluster_mode=spec.cluster_mode,
            cluster_size=spec.cluster_size,
            priority=spec.priority,
            status=SessionStatus.PENDING.name,
            status_history={
                SessionStatus.PENDING.name: datetime.now(tzutc()).isoformat(),
            },
            requested_slots=total_requested,
            occupying_slots=ResourceSlot(),
            vfolder_mounts=context.vfolder_mounts,
            environ=environ,
            tag=spec.session_tag,
            starts_at=spec.starts_at,
            batch_timeout=(int(spec.batch_timeout.total_seconds()) if spec.batch_timeout else None),
            callback_url=spec.callback_url,
            images=session_images,
            network_type=network_type,
            network_id=network_id,
            bootstrap_script=bootstrap_script,
            designated_agent_list=self._get_designated_agent_ids(
                spec=spec, kernel_config=kernel_configs
            ),
            use_host_network=scaling_group_network.use_host_network,
            timeout=timeout,
            kernels=kernel_data_list,
            dependencies=spec.dependency_sessions or [],
        )

        return session_data

    def _determine_network_config(
        self,
        spec: SessionCreationSpec,
        context: SessionCreationContext,
    ) -> tuple[NetworkType | None, str | None]:
        """Determine network type and ID from spec."""
        if spec.network:
            return NetworkType.PERSISTENT, str(spec.network.id)
        elif context.scaling_group_network.use_host_network:
            return NetworkType.HOST, None
        else:
            # Default to VOLATILE for multi-container or single-container sessions
            return NetworkType.VOLATILE, None

    async def _prepare_kernels(
        self,
        spec: SessionCreationSpec,
        session_id: SessionId,
        validated_scaling_group: AllowedScalingGroup,
        kernel_configs: list[KernelEnqueueingConfig],
        internal_data: dict[str, Any],
        vfolder_mounts: list[VFolderMount],
        context: SessionCreationContext,
        calculated_resources: CalculatedResources,
    ) -> list[KernelEnqueueData]:
        """Prepare kernel enqueue data."""
        kernel_data_list = []

        for idx, kernel_config in enumerate(kernel_configs):
            kernel_id = KernelId(uuid.uuid4())

            # Get image info
            image_ref = kernel_config.get("image_ref")
            if image_ref and hasattr(image_ref, "canonical"):
                image_info = context.image_infos.get(image_ref.canonical)
            else:
                # Fallback for string image references
                image_info = None

            # Get preopen_ports from kernel config or fall back to creation_spec
            # This follows the same pattern as in the original registry.py
            preopen_ports = kernel_config.get("creation_config", {}).get("preopen_ports")
            if preopen_ports is None:
                # Fall back to creation_spec preopen_ports (applies to all kernels)
                preopen_ports = spec.creation_spec.get("preopen_ports")
            if not preopen_ports:
                preopen_ports = []
            if not isinstance(preopen_ports, list):
                preopen_ports = []

            # Use pre-calculated resources for this kernel
            if idx < len(calculated_resources.kernel_resources):
                kernel_resource = calculated_resources.kernel_resources[idx]
                requested_slots = kernel_resource.requested_slots
                resource_opts = kernel_resource.resource_opts
                log.debug(
                    "Kernel {} (idx={}, role={}) using calculated resources: {}",
                    kernel_id,
                    idx,
                    kernel_config.get("cluster_role", "unknown"),
                    requested_slots,
                )
            else:
                # Fallback if no calculated resources
                log.warning(
                    "Kernel {} (idx={}, role={}) has no calculated resources! "
                    "calculated_resources has {} entries but need idx={}",
                    kernel_id,
                    idx,
                    kernel_config.get("cluster_role", "unknown"),
                    len(calculated_resources.kernel_resources),
                    idx,
                )
                requested_slots = ResourceSlot()
                resource_opts = {}

            # Build kernel data
            kernel_data = KernelEnqueueData(
                id=kernel_id,
                session_id=session_id,
                session_creation_id=spec.session_creation_id,
                session_name=spec.session_name,
                session_type=spec.session_type,
                cluster_mode=spec.cluster_mode,
                cluster_size=spec.cluster_size,
                cluster_role=kernel_config.get("cluster_role", DEFAULT_ROLE),
                cluster_idx=kernel_config.get("cluster_idx", idx),
                local_rank=kernel_config.get("local_rank", idx),
                cluster_hostname=kernel_config.get("cluster_hostname")
                or f"{kernel_config.get('cluster_role', DEFAULT_ROLE)}{kernel_config.get('cluster_idx', idx + 1)}",
                scaling_group=validated_scaling_group.name,
                domain_name=spec.user_scope.domain_name,
                group_id=spec.user_scope.group_id,
                user_uuid=spec.user_scope.user_uuid,
                access_key=spec.access_key,
                image=image_info.canonical if image_info else self.DEFAULT_IMAGE_NAME,
                architecture=image_info.architecture if image_info else self.DEFAULT_ARCHITECTURE,
                registry=image_info.registry if image_info else self.DEFAULT_REGISTRY,
                tag=spec.session_tag,
                starts_at=spec.starts_at,
                status=KernelStatus.PENDING.name,
                status_history={
                    KernelStatus.PENDING.name: datetime.now(tzutc()).isoformat(),
                },
                occupied_slots=ResourceSlot(),
                requested_slots=requested_slots,
                occupied_shares={},
                resource_opts=resource_opts,
                environ=[f"{k}={v}" for k, v in (kernel_config.get("environ", {}) or {}).items()]  # type: ignore[attr-defined]
                if kernel_config.get("environ")
                else [],
                bootstrap_script=kernel_config.get("bootstrap_script"),
                startup_command=kernel_config.get("startup_command"),
                internal_data=internal_data,
                callback_url=spec.callback_url,
                mounts=[mount.name for mount in vfolder_mounts],  # Legacy field
                vfolder_mounts=vfolder_mounts,
                preopen_ports=preopen_ports if isinstance(preopen_ports, list) else [],
                use_host_network=context.scaling_group_network.use_host_network,
                uid=kernel_config.get("uid") or context.container_user_info.uid,
                main_gid=kernel_config.get("main_gid") or context.container_user_info.main_gid,
                gids=kernel_config.get("supplementary_gids")
                or context.container_user_info.supplementary_gids,
            )

            kernel_data_list.append(kernel_data)

        return kernel_data_list

    def _get_designated_agent_ids(
        self,
        spec: SessionCreationSpec,
        kernel_config: list[KernelEnqueueingConfig],
    ) -> Optional[list[str]]:
        """Get pre-assigned agent for a kernel."""
        # Check if agent is specified in kernel config
        designated_agents = set()
        for kernel_cfg in kernel_config:
            if agent_id := kernel_cfg.get("agent"):
                designated_agents.add(str(agent_id))
        if designated_agents:
            return list(designated_agents)
        return spec.designated_agent_list

    def _collect_session_images(
        self,
        kernel_data_list: list[KernelEnqueueData],
    ) -> list[str]:
        """Collect unique images from kernels, with main kernel first."""
        session_images: list[str] = []

        for kernel in kernel_data_list:
            if kernel.image not in session_images:
                if kernel.cluster_role == DEFAULT_ROLE:
                    # Main kernel image goes first
                    session_images.insert(0, kernel.image)
                else:
                    session_images.append(kernel.image)

        return session_images
