import os

from pydantic import BaseModel, Field, field_validator


class PrometheusConfig(BaseModel):
    # Prometheus core settings
    hostname: str = Field(
        default="localhost", description="Prometheus hostname for service discovery"
    )
    prometheus_image_tag: str = Field(default="v3.1.0")
    port: int = Field(default=19090, description="Prometheus host bind port")
    retention_days: int = Field(default=180, description="Data retention period in days")
    data_dir: str | None = Field(
        default=None, description="Host directory path for Prometheus data storage"
    )

    # Service discovery settings
    http_sd_host: str = Field(
        default="bai-m-vip", description="HTTP service discovery endpoint hostname"
    )
    http_sd_port: int = Field(
        default=18080, description="HTTP service discovery port for dynamic target discovery"
    )
    etcd_host: str = Field(
        default="host.docker.internal", description="ETCD host address for service discovery"
    )
    etcd_port: int = Field(default=8120, description="ETCD port for service discovery")

    # Exporter targets
    redis_exporter_host: str = Field(default="host.docker.internal")
    redis_exporter_port: int = Field(default=9121)
    redis_exporter_image_tag: str = Field(
        default="v1.73.0", description="Redis Exporter container image tag"
    )
    db_exporter_host: str = Field(default="host.docker.internal")
    db_exporter_port: int = Field(default=9187)
    db_exporter_image_tag: str = Field(
        default="v0.17.1", description="PostgreSQL Exporter container image tag"
    )
    blackbox_exporter_host: str = Field(
        default="host.docker.internal",
        description="Blackbox Exporter host address",
    )
    blackbox_exporter_port: int = Field(default=9115)
    blackbox_exporter_image_tag: str = Field(
        default="v0.25.0",
        description="Blackbox Exporter container image tag",
    )
    # Compute node targets for blackbox TCP probes (agent RPC/Watcher)
    compute_node_targets: list[str] = Field(
        default_factory=list,
        description="List of compute node addresses (IP or hostname) for agent connectivity probes",
    )

    # DCGM Exporter settings — uses file-based service discovery (targets.json)
    dcgm_exporter_port: int = Field(default=9400)
    dcgm_exporter_targets: list[str] = Field(
        default_factory=list,
        description="List of compute node addresses (IP or hostname) running DCGM Exporter",
    )
    dcgm_exporter_image_tag: str = Field(
        default="3.3.0-3.2.0-ubuntu22.04", description="DCGM Exporter container image tag"
    )

    # Offline repository paths
    local_archive_path: str | None = Field(
        default=None, description="Local archive path for Prometheus image"
    )
    redis_exporter_local_archive_path: str | None = Field(
        default=None, description="Local archive path for Redis Exporter image"
    )
    db_exporter_local_archive_path: str | None = Field(
        default=None, description="Local archive path for PostgreSQL Exporter image"
    )
    blackbox_exporter_local_archive_path: str | None = Field(
        default=None, description="Local archive path for Blackbox Exporter image"
    )
    dcgm_exporter_local_archive_path: str | None = Field(
        default=None, description="Local archive path for DCGM Exporter image"
    )

    @property
    def container_image(self) -> str:
        return f"prom/prometheus:{self.prometheus_image_tag}"


class SmtpConfig(BaseModel):
    host: str = Field(description="SMTP server hostname (e.g., smtp.gmail.com)")
    port: int = Field(default=587, description="SMTP server port")
    user: str = Field(description="SMTP authentication username")
    password: str = Field(description="SMTP authentication password")
    from_address: str = Field(description="Sender email address (e.g., no-reply@backend.ai)")
    from_name: str = Field(
        default="Backend.AI Enterprise",
        description="Sender display name for alert emails",
    )
    enabled: bool = Field(default=True, description="Enable SMTP for Grafana alerting")

    @field_validator("host")
    @classmethod
    def validate_host(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("SMTP host must not be empty")
        return v

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        if not (1 <= v <= 65535):
            raise ValueError(f"SMTP port must be between 1 and 65535, got {v}")
        return v

    @field_validator("from_address")
    @classmethod
    def validate_from_address(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError(f"SMTP from_address must be a valid email address, got '{v}'")
        return v


class GrafanaConfig(BaseModel):
    grafana_image_tag: str = Field(default="12.2.1", description="Grafana container image tag")
    port: int = Field(default=3000, description="Grafana host bind port")
    admin_id: str = Field(default="admin", description="Grafana administrator username")
    admin_password: str = Field(..., description="Grafana administrator password (required)")
    data_dir: str | None = Field(
        default=None, description="Host directory path for Grafana data storage"
    )
    local_archive_path: str | None = Field(
        default=None, description="Local archive path for Grafana image"
    )
    smtp: SmtpConfig | None = Field(
        default=None, description="SMTP configuration for alert email delivery"
    )

    @property
    def container_image(self) -> str:
        return f"grafana/grafana-enterprise:{self.grafana_image_tag}"


class LokiConfig(BaseModel):
    loki_image_tag: str = Field(default="3.5.0", description="Loki container image tag")
    port: int = Field(default=3100, description="Loki host bind port")
    retention_period: str = Field(
        default="720h", description="Log retention period (e.g., 24h, 720h)"
    )
    data_dir: str | None = Field(
        default=None, description="Host directory path for Loki data storage"
    )
    local_archive_path: str | None = Field(
        default=None, description="Local archive path for Loki image"
    )

    @property
    def container_image(self) -> str:
        return f"grafana/loki:{self.loki_image_tag}"


class OTELCollectorConfig(BaseModel):
    hostname: str = Field(
        default="localhost", description="OTEL Collector hostname for service discovery"
    )
    otel_image_tag: str = Field(default="0.126.0", description="OTEL Collector container image tag")
    grpc_port: int = Field(default=4317, description="OTLP gRPC receiver port")
    http_port: int = Field(default=4318, description="OTLP HTTP receiver port")
    health_port: int = Field(default=13133, description="Health check endpoint port")
    data_dir: str | None = Field(
        default=None, description="Host directory path for OTEL Collector data storage"
    )
    local_archive_path: str | None = Field(
        default=None, description="Local archive path for OTEL Collector image"
    )

    @property
    def container_image(self) -> str:
        return f"otel/opentelemetry-collector-contrib:{self.otel_image_tag}"


class PyroscopeConfig(BaseModel):
    pyroscope_image_tag: str = Field(default="1.9.2", description="Pyroscope container image tag")
    port: int = Field(default=4040, description="Pyroscope host bind port")
    data_dir: str | None = Field(
        default=None, description="Host directory path for Pyroscope data storage"
    )
    local_archive_path: str | None = Field(
        default=None, description="Local archive path for Pyroscope image"
    )

    @property
    def container_image(self) -> str:
        return f"grafana/pyroscope:{self.pyroscope_image_tag}"


class DataSourcesConfig(BaseModel):
    # Prometheus data source
    prometheus_host: str = Field(
        default="host.docker.internal", description="Prometheus server host address"
    )
    prometheus_port: int = Field(default=9090, description="Prometheus server port")

    # PostgreSQL data source (shared by Backend.AI Core and Control Panel)
    # Uses read-only user for security (SELECT permissions only)
    postgres_host: str = Field(
        default="host.docker.internal", description="PostgreSQL server host address"
    )
    postgres_port: int = Field(default=5432, description="PostgreSQL server port")
    postgres_user: str = Field(
        default_factory=lambda: os.getenv("POSTGRES_READONLY_USER", "ronly"),
        description="PostgreSQL read-only user for monitoring",
    )
    postgres_password: str = Field(
        ...,
        description="PostgreSQL read-only user password (required for security)",
    )
    postgres_database: str = Field(default="backend", description="PostgreSQL database name")

    # Observability data sources
    pyroscope_host: str = Field(default="host.docker.internal")
    pyroscope_port: int = Field(default=4040)
    loki_host: str = Field(default="host.docker.internal")
    loki_port: int = Field(default=3100)
    tempo_host: str = Field(default="host.docker.internal")
    tempo_port: int = Field(default=3200)
