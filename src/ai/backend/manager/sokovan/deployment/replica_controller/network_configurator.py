"""Network configurator for deployment replicas."""

import logging
from typing import Optional
from uuid import UUID

from ai.backend.logging.utils import BraceStyleAdapter

from ..exceptions import NetworkConfigurationError
from ..types import NetworkConfig

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class NetworkConfigurator:
    """Configurator for network settings of deployment replicas."""

    async def configure(
        self,
        endpoint_id: UUID,
        session_name: str,
        base_config: NetworkConfig,
    ) -> NetworkConfig:
        """
        Configure network settings for a replica.

        :param endpoint_id: ID of the endpoint
        :param session_name: Name of the session
        :param base_config: Base network configuration
        :return: Configured network settings
        """
        try:
            # Validate base configuration
            self._validate_config(base_config)

            # Generate unique subdomain if needed
            subdomain = await self._generate_subdomain(
                endpoint_id,
                session_name,
                base_config.subdomain,
            )

            # Configure port mappings
            port_mappings = await self._configure_ports(
                endpoint_id,
                base_config.port_mappings,
            )

            # Create final configuration
            config = NetworkConfig(
                endpoint_id=endpoint_id,
                port_mappings=port_mappings,
                subdomain=subdomain,
            )

            log.debug(
                "Configured network for endpoint {} session {}: {}",
                endpoint_id,
                session_name,
                config,
            )

            return config

        except Exception as e:
            log.error(
                "Failed to configure network for endpoint {} session {}: {}",
                endpoint_id,
                session_name,
                str(e),
            )
            raise NetworkConfigurationError(f"Failed to configure network: {str(e)}") from e

    def _validate_config(self, config: NetworkConfig) -> None:
        """
        Validate network configuration.

        :param config: Network configuration to validate
        :raises NetworkConfigurationError: If configuration is invalid
        """
        if not config.endpoint_id:
            raise NetworkConfigurationError("Endpoint ID is required")

        if not config.port_mappings:
            raise NetworkConfigurationError("At least one port mapping is required")

        # Validate port ranges
        for name, port in config.port_mappings.items():
            if not (1 <= port <= 65535):
                raise NetworkConfigurationError(
                    f"Invalid port {port} for {name}: must be between 1 and 65535"
                )

    async def _generate_subdomain(
        self,
        endpoint_id: UUID,
        session_name: str,
        base_subdomain: Optional[str],
    ) -> Optional[str]:
        """
        Generate a unique subdomain for the replica.

        :param endpoint_id: ID of the endpoint
        :param session_name: Name of the session
        :param base_subdomain: Base subdomain to use
        :return: Generated subdomain or None
        """
        if not base_subdomain:
            return None

        # Generate unique subdomain based on session name
        # This ensures each replica has a unique network endpoint
        session_suffix = session_name.split("-")[-1][:8]
        subdomain = f"{base_subdomain}-{session_suffix}"

        return subdomain

    async def _configure_ports(
        self,
        endpoint_id: UUID,
        base_ports: dict[str, int],
    ) -> dict[str, int]:
        """
        Configure port mappings for the replica.

        :param endpoint_id: ID of the endpoint
        :param base_ports: Base port mappings
        :return: Configured port mappings
        """
        # For now, use the base ports directly
        # This can be extended to allocate dynamic ports if needed
        configured_ports = base_ports.copy()

        # Ensure standard ports are included
        if "http" not in configured_ports:
            configured_ports["http"] = 8080
        if "https" not in configured_ports:
            configured_ports["https"] = 8443

        return configured_ports
