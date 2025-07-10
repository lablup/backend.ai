from __future__ import annotations

import os
import sys
from pathlib import Path
from pprint import pformat

from ai.backend.common.config import (
    override_key,
    override_with_env,
    read_from_file,
)
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes

from .unified import StorageProxyUnifiedConfig


def load_local_config(config_path: Path | None, debug: bool = False) -> StorageProxyUnifiedConfig:
    """Load and validate the storage-proxy local configuration."""
    # Determine where to read configuration
    raw_cfg, cfg_src_path = read_from_file(config_path, "storage-proxy")
    os.chdir(cfg_src_path.parent)

    # Apply environment overrides
    override_with_env(raw_cfg, ("etcd", "namespace"), "BACKEND_NAMESPACE")
    override_with_env(raw_cfg, ("etcd", "addr"), "BACKEND_ETCD_ADDR")
    override_with_env(raw_cfg, ("etcd", "user"), "BACKEND_ETCD_USER")
    override_with_env(raw_cfg, ("etcd", "password"), "BACKEND_ETCD_PASSWORD")

    if debug:
        override_key(raw_cfg, ("debug", "enabled"), True)

    try:
        local_config = StorageProxyUnifiedConfig.model_validate(raw_cfg)
        return local_config
    except Exception as e:
        print(
            "ConfigurationError: Validation of storage-proxy local config has failed:",
            file=sys.stderr,
        )
        print(pformat(raw_cfg), file=sys.stderr)
        from ai.backend.common.config import ConfigurationError as BaseConfigError

        raise BaseConfigError(raw_cfg) from e


def load_shared_config(local_config: StorageProxyUnifiedConfig) -> AsyncEtcd:
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

    from ai.backend.common.types import HostPortPair as CommonHostPortPair

    # Convert to common HostPortPair
    addr = local_config.etcd.addr
    common_addr = CommonHostPortPair(host=addr.host, port=addr.port)

    etcd = AsyncEtcd(
        common_addr,
        local_config.etcd.namespace,
        scope_prefix_map,
        credentials=etcd_credentials,
    )
    return etcd
