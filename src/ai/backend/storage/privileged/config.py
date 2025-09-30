import os
import sys
from pathlib import Path
from pprint import pformat

from pydantic import (
    AliasChoices,
    BaseModel,
    Field,
    field_validator,
)

from ai.backend.common.config import ConfigurationError as BaseConfigError
from ai.backend.common.config import override_key, override_with_env, read_from_file
from ai.backend.logging import LogLevel

from ..config.unified import StorageProxyUnifiedConfig

DEFAULT_DAEMON_NAME = "storage-proxy"


def _is_root() -> bool:
    return os.geteuid() == 0


class PrivilegedWorkerConfig(BaseModel):
    raise_if_not_root: bool = Field(
        default=True,
        description="Raise an error if not running as root.",
        validation_alias=AliasChoices("raise-if-not-root", "raise_if_not_root"),
    )

    @field_validator("raise_if_not_root", mode="after")
    @classmethod
    def check_if_root(cls, value: bool) -> bool:
        if value and not _is_root():
            print(
                "The privileged worker must be run as root. "
                "Set `privileged-worker.raise-if-not-root` to false to override this check.",
                file=sys.stderr,
            )
            raise ValueError("Not running as root")
        return value


class StorageProxyPrivilegedWorkerConfig(StorageProxyUnifiedConfig):
    privileged_worker: PrivilegedWorkerConfig = Field(
        default_factory=PrivilegedWorkerConfig,
        description="Configuration for privileged worker.",
        validation_alias=AliasChoices("privileged-worker", "privileged_worker"),
    )


def load_local_config(
    config_path: Path | None,
    log_level: LogLevel = LogLevel.NOTSET,
) -> StorageProxyPrivilegedWorkerConfig:
    """Load and validate the privileged-storage-proxy local configuration."""
    # Determine where to read configuration
    raw_cfg, cfg_src_path = read_from_file(config_path, DEFAULT_DAEMON_NAME)
    os.chdir(cfg_src_path.parent)

    # Apply environment overrides
    override_with_env(raw_cfg, ("etcd", "namespace"), "BACKEND_NAMESPACE")
    override_with_env(raw_cfg, ("etcd", "addr"), "BACKEND_ETCD_ADDR")
    override_with_env(raw_cfg, ("etcd", "user"), "BACKEND_ETCD_USER")
    override_with_env(raw_cfg, ("etcd", "password"), "BACKEND_ETCD_PASSWORD")

    override_key(raw_cfg, ("debug", "enabled"), log_level == LogLevel.DEBUG)
    if log_level != LogLevel.NOTSET:
        override_key(raw_cfg, ("logging", "level"), log_level)
        override_key(raw_cfg, ("logging", "pkg-ns", "ai.backend"), log_level)

    try:
        local_config = StorageProxyPrivilegedWorkerConfig.model_validate(raw_cfg)
        return local_config
    except Exception as e:
        print(
            "ConfigurationError: Validation of privileged-storage-proxy local config has failed:",
            file=sys.stderr,
        )
        print(pformat(raw_cfg), file=sys.stderr)
        raise BaseConfigError(raw_cfg) from e
