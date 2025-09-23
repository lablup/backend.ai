from __future__ import annotations

import os
import sys
from pathlib import Path

from ai.backend.common.config import ConfigurationError as BaseConfigError
from ai.backend.common.config import override_key, override_with_env, read_from_file
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
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
        local_config = StorageProxyUnifiedConfig.model_validate(raw_cfg)
        return local_config
    except Exception as e:
        print(
            f"ConfigurationError: Validation of storage-proxy local config has failed, {e}",
            file=sys.stderr,
        )
        raise BaseConfigError(raw_cfg) from e


def make_etcd(local_config: StorageProxyUnifiedConfig) -> AsyncEtcd:
    """Load shared configuration from etcd."""
    etcd_credentials = None
    if local_config.etcd.user and local_config.etcd.password:
        etcd_credentials = {
            "user": local_config.etcd.user,
            "password": local_config.etcd.password,
        }

    scope_prefix_map = {
        ConfigScopes.GLOBAL: "",
        ConfigScopes.NODE: f"nodes/storage/{local_config.storage_proxy.node_id}",
    }

    etcd_config_data = local_config.etcd.to_dataclass()
    etcd = AsyncEtcd(
        [addr.to_legacy() for addr in etcd_config_data.addrs],
        local_config.etcd.namespace,
        scope_prefix_map,
        credentials=etcd_credentials,
    )
    return etcd
