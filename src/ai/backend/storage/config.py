import os
import sys
from pathlib import Path
from pprint import pformat
from typing import Any

import trafaret as t

from ai.backend.common import validators as tx
from ai.backend.common.config import (
    ConfigurationError,
    check,
    etcd_config_iv,
    override_key,
    override_with_env,
    read_from_file,
)
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.logging import logging_config_iv

from .types import VolumeInfo

_max_cpu_count = os.cpu_count()
try:
    _file_perm = (Path(__file__).parent / "server.py").stat()
    _default_uid = _file_perm.st_uid
    _default_gid = _file_perm.st_gid
except IOError:
    _default_uid = os.getuid()
    _default_gid = os.getgid()


local_config_iv = (
    t.Dict(
        {
            t.Key("storage-proxy"): t.Dict(
                {
                    t.Key("ipc-base-path", default="/tmp/backend.ai/ipc"): tx.Path(
                        type="dir", auto_create=True
                    ),
                    t.Key("node-id"): t.String,
                    t.Key("num-proc", default=_max_cpu_count): t.Int[1:_max_cpu_count],
                    t.Key("pid-file", default=os.devnull): tx.Path(
                        type="file",
                        allow_nonexisting=True,
                        allow_devnull=True,
                    ),
                    t.Key("event-loop", default="asyncio"): t.Enum("asyncio", "uvloop"),
                    t.Key("scandir-limit", default=1000): t.Int[0:],
                    t.Key("max-upload-size", default="100g"): tx.BinarySize,
                    t.Key("secret"): t.String,  # used to generate JWT tokens
                    t.Key("session-expire"): tx.TimeDuration,
                    t.Key("user", default=None): tx.UserID(
                        default_uid=_default_uid,
                    ),
                    t.Key("group", default=None): tx.GroupID(
                        default_gid=_default_gid,
                    ),
                    tx.AliasedKey(
                        ["aiomonitor-termui-port", "aiomonitor-port"], default=48300
                    ): t.ToInt[1:65535],
                    t.Key("aiomonitor-webui-port", default=49300): t.ToInt[1:65535],
                    t.Key("watcher-insock-path-prefix", default=None): t.Null | t.String(
                        allow_blank=False
                    ),
                    t.Key("watcher-outsock-path-prefix", default=None): t.Null | t.String(
                        allow_blank=False
                    ),
                    t.Key("use-watcher", default=False): t.Bool(),
                },
            ),
            t.Key("logging"): logging_config_iv,
            t.Key("api"): t.Dict(
                {
                    t.Key("client"): t.Dict(
                        {
                            t.Key("service-addr"): tx.HostPortPair(
                                allow_blank_host=True,
                            ),
                            t.Key("ssl-enabled"): t.ToBool,
                            t.Key("ssl-cert", default=None): t.Null | tx.Path(type="file"),
                            t.Key("ssl-privkey", default=None): t.Null | tx.Path(type="file"),
                        },
                    ),
                    t.Key("manager"): t.Dict(
                        {
                            t.Key("service-addr"): tx.HostPortPair(
                                allow_blank_host=True,
                            ),
                            t.Key("ssl-enabled"): t.ToBool,
                            t.Key("ssl-cert", default=None): t.Null | tx.Path(type="file"),
                            t.Key("ssl-privkey", default=None): t.Null | tx.Path(type="file"),
                            t.Key("secret"): t.String,  # used to authenticate managers
                        },
                    ),
                },
            ),
            t.Key("volume"): t.Mapping(
                t.String,
                VolumeInfo.as_trafaret(),  # volume name -> details
            ),
            t.Key("debug"): t.Dict(
                {
                    t.Key("enabled", default=False): t.ToBool,
                    t.Key("asyncio", default=False): t.ToBool,
                    t.Key("enhanced-aiomonitor-task-info", default=False): t.ToBool,
                    t.Key("log-events", default=False): t.ToBool,
                },
            ).allow_extra("*"),
        },
    )
    .merge(etcd_config_iv)
    .allow_extra("*")
)


def load_local_config(config_path: Path | None, debug: bool = False) -> dict[str, Any]:
    # Determine where to read configuration.
    raw_cfg, cfg_src_path = read_from_file(config_path, "storage-proxy")
    os.chdir(cfg_src_path.parent)

    override_with_env(raw_cfg, ("etcd", "namespace"), "BACKEND_NAMESPACE")
    override_with_env(raw_cfg, ("etcd", "addr"), "BACKEND_ETCD_ADDR")
    override_with_env(raw_cfg, ("etcd", "user"), "BACKEND_ETCD_USER")
    override_with_env(raw_cfg, ("etcd", "password"), "BACKEND_ETCD_PASSWORD")
    if debug:
        override_key(raw_cfg, ("debug", "enabled"), True)

    try:
        local_config = check(raw_cfg, local_config_iv)
        local_config["_src"] = cfg_src_path
        return local_config
    except ConfigurationError as e:
        print(
            "ConfigurationError: Validation of storage-proxy local config has failed:",
            file=sys.stderr,
        )
        print(pformat(e.invalid_data), file=sys.stderr)
        raise


def load_shared_config(local_config: dict[str, Any]) -> AsyncEtcd:
    etcd_credentials = None
    if local_config["etcd"]["user"]:
        etcd_credentials = {
            "user": local_config["etcd"]["user"],
            "password": local_config["etcd"]["password"],
        }
    scope_prefix_map = {
        ConfigScopes.GLOBAL: "",
        ConfigScopes.NODE: f"nodes/storage/{local_config['storage-proxy']['node-id']}",
    }
    etcd = AsyncEtcd(
        local_config["etcd"]["addr"],
        local_config["etcd"]["namespace"],
        scope_prefix_map,
        credentials=etcd_credentials,
    )
    return etcd
