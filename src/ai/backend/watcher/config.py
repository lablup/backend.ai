import os
import socket

import trafaret as t

from ai.backend.common import validators as tx
from ai.backend.common.config import etcd_config_iv

watcher_config_iv = (
    t.Dict({
        t.Key("watcher"): t.Dict({
            t.Key("ipc-base-path", default="/tmp/backend.ai/ipc"): tx.Path(
                type="dir", auto_create=True
            ),
            t.Key("node-id", default=f"i-watcher-{socket.gethostname()}"): t.String,
            t.Key("pid-file", default=os.devnull): tx.Path(
                type="file",
                allow_nonexisting=True,
                allow_devnull=True,
            ),
            t.Key("event-loop", default="asyncio"): t.Enum("asyncio", "uvloop"),
            t.Key("service-addr", default=("0.0.0.0", 6009)): tx.HostPortPair,
            t.Key("ssl-enabled", default=False): t.ToBool,
            t.Key("ssl-cert", default=None): t.Null | tx.Path(type="file"),
            t.Key("ssl-privkey", default=None): t.Null | tx.Path(type="file"),
            t.Key("target-service", default=None): t.Null | t.String,
            t.Key("soft-reset-available", default=False): t.Bool,
            t.Key("allowed-plugins", default=None): t.Null | tx.ToSet,
            t.Key("disabled-plugins", default=None): t.Null | tx.ToSet,
            t.Key("event"): t.Dict({
                t.Key("connect-server", default=False): t.ToBool,
                t.Key("consumer-group", default=None): t.Null | t.String,
            }),
        }).allow_extra("*"),
        t.Key("logging"): t.Any,  # checked in ai.backend.common.logging
        t.Key("debug"): t.Dict({
            t.Key("enabled", default=False): t.Bool,
            t.Key("asyncio", default=False): t.ToBool,
            t.Key("log-events", default=False): t.ToBool,
        }).allow_extra("*"),
        t.Key("module"): t.Mapping(t.String, t.Any),
    })
    .merge(etcd_config_iv)
    .allow_extra("*")
)
