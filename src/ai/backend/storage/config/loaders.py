from __future__ import annotations

import os
import sys
from pathlib import Path
from pprint import pformat

from ai.backend.common.config import ConfigurationError as BaseConfigError
from ai.backend.common.config import override_key, override_with_env, read_from_file
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.exception import BackendAIError, BackendAISchemaValidationFailed
from ai.backend.logging import LogLevel

from .unified import StorageProxyUnifiedConfig


def load_local_config(
    config_path: Path | None,
    log_level: LogLevel = LogLevel.NOTSET,
) -> StorageProxyUnifiedConfig:
    """Load and validate the storage-proxy local configuration."""
    # Determine where to read configuration
    raw_cfg, cfg_src_path = read_from_file(config_path, "storage-proxy")
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
        return StorageProxyUnifiedConfig.model_validate(raw_cfg)
    except Exception as e:
        if isinstance(e, BackendAISchemaValidationFailed):
            # The wrapped ValidationError's message embeds input values; its errors() does not.
            detail = pformat(e.errors())
        elif isinstance(e, BackendAIError):
            # Raised directly by the after-validators with a fixed message.
            detail = str(e)
        else:
            detail = type(e).__name__
        print(
            "ConfigurationError: Validation of storage-proxy local config has failed:",
            detail,
            sep="\n",
            file=sys.stderr,
        )
        # Neither the raw config nor the chained error may reach a traceback: both hold secrets.
        raise BaseConfigError({}) from None


def make_etcd(local_config: StorageProxyUnifiedConfig) -> AsyncEtcd:
    """Load shared configuration from etcd."""
    scope_prefix_map = {
        ConfigScopes.GLOBAL: "",
        ConfigScopes.NODE: f"nodes/storage/{local_config.storage_proxy.node_id}",
    }
    return AsyncEtcd.create_from_config(local_config.etcd.to_dataclass(), scope_prefix_map)
