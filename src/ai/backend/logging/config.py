from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any

import trafaret as t

from .types import (
    DirPathTrafaret,
    LogFormat,
    LogLevel,
    SimpleBinarySizeTrafaret,
)

default_pkg_ns: dict[str, LogLevel] = {
    "": LogLevel.WARNING,
    "ai.backend": LogLevel.INFO,
    "tests": LogLevel.DEBUG,
}

logging_config_iv = t.Dict({
    t.Key("level", default=LogLevel.INFO): LogLevel.as_trafaret(),
    t.Key("pkg-ns", default=default_pkg_ns): t.Mapping(
        t.String(allow_blank=True), LogLevel.as_trafaret()
    ),
    t.Key("drivers", default=["console"]): t.List(
        t.Enum(
            "console",
            "logstash",
            "file",
            "graylog",
        )
    ),
    t.Key(
        "console",
        default={
            "colored": None,
            "format": LogFormat.VERBOSE,
        },
    ): t.Dict({
        t.Key("colored", default=None): t.Null | t.ToBool,
        t.Key("format", default=LogFormat.VERBOSE): LogFormat.as_trafaret(),
    }).allow_extra("*"),
    t.Key("file", default=None): t.Null
    | t.Dict({
        t.Key("path"): DirPathTrafaret(auto_create=True),
        t.Key("filename"): t.String,
        t.Key("backup-count", default=5): t.ToInt[1:100],
        t.Key("rotation-size", default="10M"): SimpleBinarySizeTrafaret,
        t.Key("format", default=LogFormat.VERBOSE): LogFormat.as_trafaret(),
    }).allow_extra("*"),
    t.Key("logstash", default=None): t.Null
    | t.Dict({
        t.Key("endpoint"): t.Tuple(t.String, t.ToInt[1:65535])
        | t.Dict({
            t.Key("host"): t.String,
            t.Key("port"): t.ToInt[1:65535],
        }),
        t.Key("protocol", default="tcp"): t.Enum("zmq.push", "zmq.pub", "tcp", "udp"),
        t.Key("ssl-enabled", default=True): t.ToBool,
        t.Key("ssl-verify", default=True): t.ToBool,
        # NOTE: logstash does not have format option.
    }).allow_extra("*"),
    t.Key("graylog", default=None): t.Null
    | t.Dict({
        t.Key("host"): t.String,
        t.Key("port"): t.ToInt[1024:65535],
        t.Key("level", default=LogLevel.INFO): LogLevel.as_trafaret(),
        t.Key("ssl-verify", default=False): t.Bool,
        t.Key("ca-certs", default=None): t.Null | t.String(allow_blank=True),
        t.Key("keyfile", default=None): t.Null | t.String(allow_blank=True),
        t.Key("certfile", default=None): t.Null | t.String(allow_blank=True),
        t.Key("fqdn", default=True): t.ToBool,
        t.Key("localname", default=None): t.Null | t.String(),
    }).allow_extra("*"),
}).allow_extra("*")


def override_key(table: MutableMapping[str, Any], key_path: tuple[str, ...], value: Any):
    for k in key_path[:-1]:
        if k not in table:
            table[k] = {}
        table = table[k]
    table[key_path[-1]] = value
