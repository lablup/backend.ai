from pydantic import BaseModel, Field


class DoctorConfig(BaseModel):
    version: str = Field(
        default="latest",
        description="Backend.AI Doctor version to install (e.g., 'v0.7.0' or 'latest')",
    )

    customer_token: str = Field(
        default="",
        description="Customer authentication token for Lambda email notifications",
    )

    enable_watchdog: bool = Field(
        default=True,
        description="Enable systemd watchdog service for automated monitoring",
    )

    local_archive_path: str | None = Field(
        default=None,
        description="Local archive path for Doctor binary (for offline/airgap installation)",
    )

    class Config:
        extra = "forbid"
