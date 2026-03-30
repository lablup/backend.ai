from typing import Literal

from pydantic import BaseModel, Field


class PostgreSQLConfig(BaseModel):
    hostname: str = "bai-m-vip"
    port: int = 8100
    # NOTE: Core DB user other than `postgres` will complicate "non-HA" DB operation.
    user: str = "postgres"
    password: str
    db_name: str = "backend"

    container_image: str = "postgres:16.9-alpine"
    container_name: str = "bai-postgres"
    local_archive_path: str | None = None


class EtcdConfig(BaseModel):
    advertised_client_ip: str = "0.0.0.0"
    advertised_client_port: int = 8120
    connect_client_ip: str = "bai-m1"

    container_image: str = "quay.io/coreos/etcd:v3.5.21"
    container_name: str = "bai-etcd"
    local_archive_path: str | None = None


class RedisConfig(BaseModel):
    hostname: str = "bai-m-vip"
    port: int = 8110
    password: str

    container_image: str
    container_name: str = "bai-redis"
    local_archive_path: str | None = None


class EtcdHAClusterNodeConfig(BaseModel):
    hostname: str
    client_ip: str
    client_port: int = 8121
    ssh_ip: str
    peer_ip: str
    peer_port: int = 8321
    node_number: int


class EtcdHAConfig(BaseModel):
    """Unified ETCD HA configuration that combines cluster and gRPC proxy"""

    name: str = "default"
    cluster_nodes: list[EtcdHAClusterNodeConfig] = Field(min_length=3)
    container_image: str = "quay.io/coreos/etcd:v3.4.22"
    container_name_prefix: str = "bai-etcd"
    grpc_container_image: str = "cr.backend.ai/halfstack/etcd-grpcproxy:v3.4.22"
    grpc_container_name_prefix: str = "bai-etcd-grpc"
    pids_limit: int = 1000

    # gRPC proxy configuration
    grpc_service_ip: str = "0.0.0.0"
    grpc_service_port: int = 8120

    local_archive_path: str | None = None
    grpc_local_archive_path: str | None = None

    def get_initial_cluster_string(self) -> str:
        """Generate the initial cluster string for ETCD configuration"""
        return ",".join([
            f"etcd{node.node_number}=http://etcd{node.node_number}:{node.peer_port}"
            for node in self.cluster_nodes
        ])

    def get_cluster_endpoints(self) -> str:
        """Generate the cluster endpoints string for client connections"""
        return ",".join([
            f"etcd{node.node_number}:{node.client_port}" for node in self.cluster_nodes
        ])


class PostgresHAClusterNodeConfig(BaseModel):
    hostname: str
    ip: str
    etcd_client_port: int = 8126
    etcd_peer_port: int = 8326
    pg_api_port: int = 8111
    pg_sql_port: int = 8101
    node_number: int


class PostgresHAConfig(BaseModel):
    name: str = "default"  # Instance name for directory and service naming
    cluster_nodes: list[PostgresHAClusterNodeConfig] = Field(min_length=3)
    service_name: str = "postgresql"
    pg_major_version: str = "15"

    # PostgreSQL connection ports
    pg_active_port: int = 8100
    pg_standby_port: int = 8105

    # PostgreSQL authentication
    pg_replicator_id: str = "replicator"
    pg_replicator_password: str
    pg_superuser_id: str = "postgres"
    pg_superuser_password: str
    pg_rewind_id: str = "rewind"
    pg_rewind_password: str
    shared_preload_libraries: str = ""

    # Resource limits
    cpu_count: int = 4
    memory_limit: str = "8g"
    shm_size: str = "2g"

    # ETCD resource limits
    etcd_cpu_count: int = 1
    etcd_memory_limit: str = "1g"

    # HAProxy configuration
    haproxy_stat_port: int = 7000
    haproxy_container_image: str | None = None
    haproxy_container_name_prefix: str = "bai-postgres-haproxy"

    container_image: str = "cr.backend.ai/halfstack/postgres_ha:15.2"
    container_name_prefix: str = "bai-postgres"
    etcd_container_image: str = "quay.io/coreos/etcd:v3.5.21"
    etcd_container_name_prefix: str = "bai-postgres-etcd"
    local_archive_path: str | None = None
    etcd_local_archive_path: str | None = None
    haproxy_local_archive_path: str | None = None


class RedisHAClusterNodeConfig(BaseModel):
    hostname: str
    ip: str
    port: int = 8112
    ssh_ip: str
    node_number: int


class RedisHAConfig(BaseModel):
    """Unified Redis HA configuration that combines cluster, sentinel, and HAProxy"""

    name: str = "default"
    cluster_nodes: list[RedisHAClusterNodeConfig] = Field(min_length=3)
    password: str

    # Container images
    container_image: str
    haproxy_container_image: str | None = None

    # Service ports
    haproxy_service_port: int = 8110
    haproxy_stat_port: int = 9000
    sentinel_port: int = 8114

    # Resource limits
    redis_cpu_count: int = 2
    redis_memory_limit: str = "4g"
    haproxy_cpu_count: int = 1
    haproxy_memory_limit: str = "2g"
    sentinel_cpu_count: int = 1
    sentinel_memory_limit: str = "1g"
    pids_limit: int = 1000

    # Redis configuration
    min_slaves_to_write: int = 1
    min_slaves_max_lag: int = 10

    # Sentinel configuration
    sentinel_quorum: int = 2
    sentinel_down_after_milliseconds: int = 3000
    sentinel_failover_timeout: int = 30000
    sentinel_parallel_syncs: int = 2

    local_archive_path: str | None = None
    haproxy_local_archive_path: str | None = None

    # Container naming configuration
    container_name_prefix: str = "bai-redis"
    sentinel_container_name_prefix: str = "bai-redis-sentinel"
    haproxy_container_name_prefix: str = "bai-redis-haproxy"

    def get_master_node(self) -> RedisHAClusterNodeConfig:
        """Get the master node (node1)"""
        return next(node for node in self.cluster_nodes if node.node_number == 1)

    def get_slave_nodes(self) -> list[RedisHAClusterNodeConfig]:
        """Get all slave nodes (node2, node3, ...)"""
        return [node for node in self.cluster_nodes if node.node_number != 1]

    def get_redis_hosts_list(self) -> str:
        """Generate Redis hosts list for docker extra_hosts"""
        return ",".join([f"redis{node.node_number}:{node.ip}" for node in self.cluster_nodes])


class HiveGatewayClusterNodeConfig(BaseModel):
    """Configuration for a single Hive Gateway node in HA cluster."""

    name: str = Field(description="Node identifier (e.g., 'hive_gateway_1')")
    hostname: str = Field(description="Hostname for this gateway node (e.g., 'bai-gw1')")
    ip: str = Field(description="IP address for this gateway node")


class HiveGatewayConfig(BaseModel):
    """Configuration for GraphQL Federation Router (Hive Gateway or Apollo Router).

    Provides a unified GraphQL endpoint that federates multiple Manager GraphQL
    subgraphs (Graphene legacy API, Strawberry new API).

    Backend.AI 25.15 uses Apollo Router, while post-25.15 uses Hive Gateway.
    Set ``router_type`` to select the appropriate router.
    """

    name: str = Field(default="default", description="Instance name for service directory naming.")

    enabled: bool = Field(
        default=True,
        description="Enable GraphQL Router deployment. When enabled, Webserver routes "
        "GraphQL through the router instead of directly to Manager.",
    )

    # Router type selection
    router_type: Literal["apollo", "hive"] = Field(
        default="hive",
        description="Router type: 'hive' for Hive Gateway (post-25.15), "
        "'apollo' for Apollo Router (25.15).",
    )

    # Container configuration
    port: int = Field(default=4000, description="Port for GraphQL Router service.")
    container_image: str = Field(
        default="ghcr.io/graphql-hive/gateway:2.1.12",
        description="Docker image for Hive Gateway (used when router_type='hive').",
    )
    local_archive_path: str | None = Field(
        default=None,
        description="Local path to Hive Gateway container image archive for offline installation.",
    )

    # Apollo Router configuration (used when router_type='apollo')
    apollo_container_image: str = Field(
        default="ghcr.io/apollographql/router:v1.61.9",
        description="Docker image for Apollo Router (used when router_type='apollo').",
    )
    apollo_local_archive_path: str | None = Field(
        default=None,
        description="Local path to Apollo Router container image archive for offline installation.",
    )

    # Manager connection
    manager_hostname: str = Field(
        default="bai-manager",
        description="Hostname alias for Manager. Resolved via extra_hosts in Docker Compose.",
    )
    manager_graphql_port: int = Field(
        default=8091,
        description="Manager's GraphQL port (typically 8091 for direct, or HAProxy port).",
    )

    # External connectivity
    advertised_hostname: str = Field(
        default="localhost",
        description="Hostname/IP for co-located services (e.g., Webserver) to connect to Gateway. "
        "Defaults to localhost since Hive Gateway is deployed on the same nodes as Webserver.",
    )

    # HA Configuration (HAProxy is included in docker-compose when cluster_nodes is set)
    haproxy_container_image: str = Field(
        default="haproxy:2.9-alpine", description="HAProxy container image for HA deployment."
    )
    haproxy_local_archive_path: str | None = Field(
        default=None,
        description="Local path to HAProxy container image archive for offline installation.",
    )
    cluster_nodes: list[HiveGatewayClusterNodeConfig] = Field(
        default_factory=list,
        description="List of Hive Gateway nodes for HA load balancing. "
        "When set (2+ nodes), HAProxy is deployed.",
    )

    # Supergraph configuration
    supergraph_path: str = Field(
        default="", description="Path to pre-generated supergraph.graphql file."
    )
    gateway_config_path: str = Field(
        default="",
        description="Path to gateway.config.ts file on deployment host. If empty, template is used.",
    )
