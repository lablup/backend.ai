from __future__ import annotations

from enum import Enum
from ipaddress import IPv4Address
from typing import Any, Self
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from ai.backend.install.pyinfra.configs.halfstack import RedisHAConfig
from ai.backend.install.pyinfra.defs import _to_ipv4_or_none


class AcceleratorType(str, Enum):
    CPU = "cpu"
    CUDA = "cuda"
    ROCM = "rocm"
    TPU = "tpu"
    IPU = "ipu"
    ATOM = "atom"
    ATOM_PLUS = "atom_plus"
    ATOM_MAX = "atom_max"
    LPU = "lpu"


class LicenseServerConfig(BaseModel):
    """License server configuration (enterprise feature - schema only in OSS).

    This config is schema-only in the OSS package. Deployment requires
    backend.ai-installer (enterprise).
    """

    enabled: bool = Field(
        default=False,
        description="Always False in OSS. Enterprise installer sets to True.",
    )
    hostname: str = "bai-m1"
    port: int = 6099
    license_type: str = "fixed"  # Options: fixed, floating, floatingv2

    hwtool_binary_uri: str = "http://bai-repo:9200/license/hwtool.linux.amd64.bin"
    licensed_binary_uri: str = "http://bai-repo:9200/license/licensed.linux.amd64.bin"
    license_json_uri: str = "http://bai-repo:9200/license/license.json"

    model_config = {
        "json_schema_extra": {
            "enterprise": True,
            "requires": "backend.ai-installer",
        }
    }


class BackendAICoreConfig(BaseModel):
    version: str = "24.3.10"
    vfroot_path: str = "/vfroot"
    activator_path: str | None = None


class ManagerConfig(BaseModel):
    port: int = 8081
    haproxy_service_port: int | None = None
    haproxy_container_image: str | None = None
    cluster_nodes: list[dict] = []
    client_connect_ip: str = "bai-m1"
    num_proc: int = Field(
        default=4,
        description="Number of worker processes. Auto-adjusted to min(cpu_count, num_proc) during deployment.",
    )
    db_pool_size: int = Field(
        default=8,
        ge=1,
        description="DB connection pool size per process. Total connections = pool_size * num_proc.",
    )
    internal_host: str = "bai-m1"
    internal_port: int = 18080

    default_project_uuid: UUID = UUID("2de2b969-1d04-48a6-af16-0bc8adb3c831")
    superadmin_uuid: UUID = UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4")
    superadmin_username: str = "admin"
    superadmin_email: str = "admin@backend.ai"
    superadmin_password: str
    superadmin_access_key: str
    superadmin_secret_key: str
    user_uuid: UUID = UUID("dfa9da54-4b28-432f-be29-c0d680c7a412")
    user_username: str = "user"
    user_email: str = "user@backend.ai"
    user_password: str
    user_access_key: str
    user_secret_key: str


class WebserverConfig(BaseModel):
    port: int = 8080
    haproxy_service_port: int | None
    haproxy_container_image: str | None = None
    cluster_nodes: list[dict] = []

    # Resource limits
    max_cpu_cores_per_container: int = 64
    max_memory_per_container: int = 512  # GB
    max_cuda_devices_per_container: int = 8
    max_cuda_shares_per_container: int = 8
    max_shm_per_container: int = 128  # MB
    max_file_upload_size: int = 12884901888  # bytes (12GB)


class StorageProxyConfig(BaseModel):
    port: int = 6021
    manager_port: int = 6022
    haproxy_service_port: int | None = None
    haproxy_manager_service_port: int | None = None
    haproxy_container_image: str | None = None
    manager_facing_port: int | None = None
    client_endpoint: str
    manager_endpoint: str = "http://bai-m1:6022"
    manager_token: str
    jwt_secret: str
    name: str = "sp1"
    volume_names: str = "nas"
    internal_host: str = "0.0.0.0"
    internal_port: int = 16023
    announce_internal_host: str = "bai-m1"
    announce_internal_port: int = 16023
    cluster_nodes: list[dict] = []


class AgentConfig(BaseModel):
    accelerator_type: str | AcceleratorType = Field(default=AcceleratorType.CUDA)
    resource_group: str = "default"
    resource_group_type: str = Field(
        default="compute", description="Type of resource group: compute or storage"
    )
    rpc_listen_ip: str | IPv4Address | None = Field(default=None)
    rpc_advertised_ip: str | IPv4Address | None = Field(default=None)
    announce_internal_host: str | IPv4Address | None = Field(default=None)
    announce_internal_port: int = 6003
    metadata_server_port: int = 20128
    container_port_range: list[int] = Field(default_factory=lambda: [30000, 31000])

    accelerator_cuda_path: str | None = None
    accelerator_atom_path: str | None = None

    # Scratch storage configuration
    scratch_type: str = Field(default="hostdir", description="Scratch storage type")
    scratch_root: str = Field(default="./scratches", description="Scratch storage root path")
    scratch_size: str = Field(default="10G", description="Scratch storage size")

    @field_validator("scratch_type")
    def validate_scratch_type(cls, v: Any) -> str:
        allowed_types = ["hostdir", "hostfile", "memory", "k8s-nfs"]
        if v not in allowed_types:
            raise ValueError(f"scratch_type must be one of: {allowed_types}")
        return v

    @field_validator("resource_group_type")
    def validate_resource_group_type(cls, v: Any) -> str:
        allowed_types = ["compute", "storage"]
        if v not in allowed_types:
            raise ValueError(f"resource_group_type must be one of: {allowed_types}")
        return v

    @field_validator("accelerator_type")
    def ensure_accelerator_type(cls, v: Any) -> AcceleratorType:
        if isinstance(v, str):
            return AcceleratorType(v)
        return v

    @field_validator("rpc_listen_ip", "rpc_advertised_ip", "announce_internal_host")
    def validate_ip(cls, v: Any) -> IPv4Address | None:
        return _to_ipv4_or_none(v)

    @model_validator(mode="after")
    def set_advertised_ip(self) -> Self:
        if self.rpc_advertised_ip is None and self.rpc_listen_ip is not None:
            self.rpc_advertised_ip = self.rpc_listen_ip
        if self.announce_internal_host is None and self.rpc_advertised_ip is not None:
            self.announce_internal_host = self.rpc_advertised_ip
        return self

    @field_validator("container_port_range")
    def validate_container_port_range(cls, v: Any) -> list[int]:
        if len(v) != 2 or not all(isinstance(p, int) for p in v):
            raise ValueError("container_port_range must be a list of two integers")
        if v[0] >= v[1]:
            raise ValueError("First port in container_port_range must be less than the second")
        if any(port < 1024 or port > 65535 for port in v):
            raise ValueError("Port numbers must be between 1024 and 65535")
        return v


class AppProxyConfig(BaseModel):
    shared_key: str
    jwt_secret: str
    permit_hash_secret: str

    db_user: str = "wsproxy"
    db_password: str
    db_name: str = "wsproxy"

    coordinator_scheme: str = "http"
    coordinator_hostname: str = "bai-m1"
    coordinator_port: int = 10200
    coordinator_advertised_hostname: str

    worker_node_number: int = 1

    worker_interactive_advertised_hostname: str
    worker_interactive_port: int = 10201
    worker_interactive_app_port_start: int = 10205
    worker_interactive_app_port_end: int = 10500
    worker_interactive_aiomonitor_termui_port: int = 28600
    worker_interactive_aiomonitor_webui_port: int = 29600

    worker_tcp_advertised_hostname: str
    worker_tcp_port: int = 10202
    worker_tcp_app_port_start: int = 10501
    worker_tcp_app_port_end: int = 10600
    worker_tcp_aiomonitor_termui_port: int = 28601
    worker_tcp_aiomonitor_webui_port: int = 29601

    worker_inference_advertised_hostname: str
    worker_inference_port: int = 10203
    worker_inference_app_port_start: int = 10601
    worker_inference_app_port_end: int = 10700
    worker_inference_aiomonitor_termui_port: int = 28602
    worker_inference_aiomonitor_webui_port: int = 29602

    webserver_endpoint: str = "http://bai-m1:8080"

    traefik_archive_url: str | None = None
    traefik_plugin_url: str | None = None


class ControlPanelConfig(BaseModel):
    """Control Panel configuration (enterprise feature - schema only in OSS).

    This config is schema-only in the OSS package. Deployment requires
    backend.ai-installer (enterprise).
    """

    enabled: bool = Field(
        default=False,
        description="Always False in OSS. Enterprise installer sets to True.",
    )
    version: str = "24.03.9"
    port: int = 8443
    archive_name: str = f"control-panel-prod-{version}"
    archive_uri: str = f"http://bai-repo:9200/docker/{archive_name}.zip"
    allowed_hosts: str = "*"
    csrf_trusted_origins: list[str] = Field(default_factory=list)
    manager_endpoint: str = ""
    skip_sslcert_validation: bool = True
    manager_monitor_endpoints: list[str] = Field(default_factory=list)
    technical_support_until: str = ""

    # External PostgreSQL configuration (for dedicated CP database cluster)
    use_external_postgres: bool = False
    external_postgres_host: str | None = None
    external_postgres_port: int | None = None
    external_postgres_db: str | None = None
    external_postgres_user: str | None = None
    external_postgres_password: str | None = None

    # Embedded postgres exposed port (for debugging/external access)
    postgres_exposed_port: int = 8150

    # External Redis configuration (via Sentinel)
    use_external_redis: bool = False
    redis_ha_config: RedisHAConfig | None = None
    redis_sentinel_master_name: str | None = None
    redis_db: int = 15  # Control Panel dedicated Redis DB

    # HA mode configuration
    ha_mode: bool = False
    node_number: int = 1  # 1 = first node (runs migration/admin creation/celerybeat)
    celerybeat_enabled: bool = True

    # Docker extra_hosts for hostname→IP resolution inside containers
    # e.g., {"bai-redis-vip": "10.0.0.100", "bai-cp-db-vip": "10.0.0.101"}
    docker_extra_hosts: dict[str, str] = Field(default_factory=dict)

    model_config = {
        "json_schema_extra": {
            "enterprise": True,
            "requires": "backend.ai-installer",
        }
    }

    @model_validator(mode="after")
    def validate_external_services(self) -> Self:
        """Validate external service configuration consistency."""
        if self.use_external_redis:
            if self.redis_ha_config is None:
                raise ValueError("redis_ha_config required when use_external_redis=True")
            if not self.redis_sentinel_master_name:
                raise ValueError("redis_sentinel_master_name required when use_external_redis=True")
        if self.use_external_postgres:
            missing = [
                f
                for f in (
                    "external_postgres_host",
                    "external_postgres_port",
                    "external_postgres_db",
                    "external_postgres_user",
                )
                if not getattr(self, f, None)
            ]
            if missing:
                raise ValueError(
                    f"When use_external_postgres=True, the following fields are required: {', '.join(missing)}"
                )
        return self

    def get_sentinel_url(self) -> str:
        """Generate Sentinel URL for Django/Celery.

        Format: sentinel://[:password@]host1:port1;host2:port2;.../db?master=mastername
        Uses semicolons as host separators (required by kombu's sentinel transport).

        Returns:
            Empty string if no redis_ha_config, otherwise full sentinel:// URL
        """
        if not self.redis_ha_config:
            return ""
        sentinels = ";".join([
            f"{n.ip}:{self.redis_ha_config.sentinel_port}"
            for n in self.redis_ha_config.cluster_nodes
        ])
        if self.redis_ha_config.password:
            return f"sentinel://:{self.redis_ha_config.password}@{sentinels}/{self.redis_db}?master={self.redis_sentinel_master_name}"
        return f"sentinel://{sentinels}/{self.redis_db}?master={self.redis_sentinel_master_name}"

    def is_first_node(self) -> bool:
        """Check if this is the first node (responsible for migration/admin/celerybeat).

        Returns:
            True if node_number is 1, False otherwise
        """
        return self.node_number == 1
