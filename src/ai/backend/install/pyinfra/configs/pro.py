from pydantic import BaseModel, Field


class FastTrackConfig(BaseModel):
    """FastTrack workflow engine configuration (enterprise feature - schema only in OSS).

    This config is schema-only in the OSS package. Deployment requires
    backend.ai-installer (enterprise).
    """

    enabled: bool = Field(
        default=False,
        description="Always False in OSS. Enterprise installer sets to True.",
    )
    version: str = "24.09.1"
    port: int = 9500
    endpoint: str = "http://bai-m1:9500"  # public endpoint
    allowed_hosts: str = "*"
    jwt_secret: str = ""  # Required in enterprise

    manager_endpoint: str = "http://bai-m1:8081"
    webserver_endpoint: str = "http://bai-m1:8080"  # public endpoint
    redis_url: str = "redis://redis:6379/0"
    redis_event_stream_url: str = "redis://redis:6379/1"
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "workflow"
    postgres_user: str = "workflow"
    postgres_password: str = ""  # Required in enterprise

    archive_name: str = f"backend.ai-fasttrack-{version}-linux-amd64.release"
    archive_uri: str = f"http://bai-repo:9200/docker/{archive_name}.tar.gz"

    model_config = {
        "json_schema_extra": {
            "enterprise": True,
            "requires": "backend.ai-installer",
        }
    }
