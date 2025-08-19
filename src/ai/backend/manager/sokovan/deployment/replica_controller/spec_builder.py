"""Spec builder for creating session specifications."""

import logging
from typing import Optional
from uuid import UUID

from ai.backend.common.types import (
    ClusterMode,
    ImageAlias,
    ResourceSlot,
    SessionTypes,
    VFolderMount,
)
from ai.backend.logging.utils import BraceStyleAdapter

from ..types import NetworkConfig
from .types import SessionEnqueueSpec

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class SpecBuilder:
    """Builder for creating session enqueue specifications."""

    def build(
        self,
        endpoint_id: UUID,
        session_name: str,
        session_type: SessionTypes,
        image: ImageAlias,
        resources: ResourceSlot,
        mounts: list[VFolderMount],
        environ: dict[str, str],
        scaling_group: str,
        cluster_mode: ClusterMode,
        cluster_size: int,
        network_config: NetworkConfig,
        startup_command: Optional[str] = None,
        bootstrap_script: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> SessionEnqueueSpec:
        """
        Build a complete session enqueue specification.

        :param endpoint_id: ID of the endpoint
        :param session_name: Name of the session
        :param session_type: Type of the session
        :param image: Container image to use
        :param resources: Resource requirements
        :param mounts: Volume mounts
        :param environ: Environment variables
        :param scaling_group: Scaling group to use
        :param cluster_mode: Cluster mode
        :param cluster_size: Size of the cluster
        :param network_config: Network configuration
        :param startup_command: Optional startup command
        :param bootstrap_script: Optional bootstrap script
        :param tag: Optional tag
        :return: Complete session enqueue specification
        """
        # Add endpoint-specific environment variables
        enhanced_environ = self._enhance_environ(environ, endpoint_id, network_config)

        # Add endpoint-specific mounts if needed
        enhanced_mounts = self._enhance_mounts(mounts, endpoint_id)

        # Build the specification
        spec = SessionEnqueueSpec(
            endpoint_id=endpoint_id,
            session_name=session_name,
            session_type=session_type,
            image=image,
            resources=resources,
            mounts=enhanced_mounts,
            environ=enhanced_environ,
            scaling_group=scaling_group,
            cluster_mode=cluster_mode,
            cluster_size=cluster_size,
            network_config=network_config,
            startup_command=startup_command,
            bootstrap_script=bootstrap_script,
            tag=tag,
        )

        log.debug("Built session spec for endpoint {}: {}", endpoint_id, spec)
        return spec

    def _enhance_environ(
        self,
        environ: dict[str, str],
        endpoint_id: UUID,
        network_config: NetworkConfig,
    ) -> dict[str, str]:
        """
        Enhance environment variables with endpoint-specific values.

        :param environ: Base environment variables
        :param endpoint_id: ID of the endpoint
        :param network_config: Network configuration
        :return: Enhanced environment variables
        """
        enhanced = environ.copy()

        # Add endpoint ID
        enhanced["BACKEND_ENDPOINT_ID"] = str(endpoint_id)

        # Add network configuration
        if network_config.subdomain:
            enhanced["BACKEND_ENDPOINT_SUBDOMAIN"] = network_config.subdomain

        # Add port mappings
        for name, port in network_config.port_mappings.items():
            enhanced[f"BACKEND_PORT_{name.upper()}"] = str(port)

        return enhanced

    def _enhance_mounts(
        self,
        mounts: list[VFolderMount],
        endpoint_id: UUID,
    ) -> list[VFolderMount]:
        """
        Enhance mounts with endpoint-specific volumes if needed.

        :param mounts: Base volume mounts
        :param endpoint_id: ID of the endpoint
        :return: Enhanced volume mounts
        """
        # For now, just return the original mounts
        # This can be extended to add endpoint-specific volumes
        return mounts
