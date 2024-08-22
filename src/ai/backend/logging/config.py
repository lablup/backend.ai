from __future__ import annotations

import trafaret as t

from .types import LogFormat, LogLevel

loglevel_iv = t.Enum(*LogLevel)
logformat_iv = t.Enum(*LogFormat)

default_pkg_ns = {
    "": "WARNING",
    "ai.backend": "INFO",
    "tests": "DEBUG",
}

logging_config_iv = t.Dict({
    t.Key("level", default=LogLevel.INFO): loglevel_iv,
    t.Key("pkg-ns", default=default_pkg_ns): t.Mapping(t.String(allow_blank=True), loglevel_iv),
    t.Key("drivers", default=["console"]): t.List(t.Enum("console", "logstash", "file", "graylog")),
    t.Key(
        "console",
        default={
            "colored": None,
            "format": "verbose",
        },
    ): t.Dict({
        t.Key("colored", default=None): t.Null | t.Bool,
        t.Key("format", default="verbose"): logformat_iv,
    }).allow_extra("*"),
    t.Key("file", default=None): t.Null
    | t.Dict({
        t.Key("path"): tx.Path(type="dir", auto_create=True),
        t.Key("filename"): t.String,
        t.Key("backup-count", default=5): t.Int[1:100],
        t.Key("rotation-size", default="10M"): tx.BinarySize,
        t.Key("format", default="verbose"): logformat_iv,
    }).allow_extra("*"),
    t.Key("logstash", default=None): t.Null
    | t.Dict({
        t.Key("endpoint"): tx.HostPortPair,
        t.Key("protocol", default="tcp"): t.Enum("zmq.push", "zmq.pub", "tcp", "udp"),
        t.Key("ssl-enabled", default=True): t.Bool,
        t.Key("ssl-verify", default=True): t.Bool,
        # NOTE: logstash does not have format option.
    }).allow_extra("*"),
    t.Key("graylog", default=None): t.Null
    | t.Dict({
        t.Key("host"): t.String,
        t.Key("port"): t.ToInt[1024:65535],
        t.Key("level", default="INFO"): loglevel_iv,
        t.Key("ssl-verify", default=False): t.Bool,
        t.Key("ca-certs", default=None): t.Null | t.String(allow_blank=True),
        t.Key("keyfile", default=None): t.Null | t.String(allow_blank=True),
        t.Key("certfile", default=None): t.Null | t.String(allow_blank=True),
        t.Key("fqdn", default=True): t.Bool,
        t.Key("localname", default=None): t.Null | t.String(),
    }).allow_extra("*"),
}).allow_extra("*")
