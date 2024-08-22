from __future__ import annotations

from collections.abc import MutableMapping
from decimal import Decimal
from pathlib import Path
from typing import Any

import trafaret as t

from .types import LogFormat, LogLevel

loglevel_iv = t.Enum(*LogLevel)
logformat_iv = t.Enum(*LogFormat)

default_pkg_ns: dict[str, LogLevel] = {
    "": LogLevel.WARNING,
    "ai.backend": LogLevel.INFO,
    "tests": LogLevel.DEBUG,
}


class SimpleBinarySizeTrafaret(t.Trafaret):
    suffix_map = {
        "y": 2**80,  # yotta
        "z": 2**70,  # zetta
        "e": 2**60,  # exa
        "p": 2**50,  # peta
        "t": 2**40,  # tera
        "g": 2**30,  # giga
        "m": 2**20,  # mega
        "k": 2**10,  # kilo
        " ": 1,
    }
    endings = ("ibytes", "ibyte", "ib", "bytes", "byte", "b")

    def check_and_return(self, value: str) -> int:
        orig_value = value
        value = value.strip().replace("_", "")
        try:
            return int(value)
        except ValueError:
            value = value.lower()
            dec_expr: Decimal
            try:
                for ending in self.endings:
                    if (stem := value.removesuffix(ending)) != value:
                        suffix = stem[-1]
                        dec_expr = Decimal(stem[:-1])
                        break
                else:
                    # when there is suffix without scale (e.g., "2K")
                    if not str.isnumeric(value[-1]):
                        suffix = value[-1]
                        dec_expr = Decimal(value[:-1])
                    else:
                        # has no suffix and is not an integer
                        # -> fractional bytes (e.g., 1.5 byte)
                        raise ValueError("Fractional bytes are not allowed")
            except ArithmeticError:
                raise ValueError("Unconvertible value", orig_value)
            try:
                multiplier = self.suffix_map[suffix]
            except KeyError:
                raise ValueError("Unconvertible value", orig_value)
            return int(dec_expr * multiplier)


class DirPathTrafaret(t.Trafaret):
    def __init__(
        self,
        *,
        auto_create: bool = False,
    ) -> None:
        super().__init__()
        self._auto_create = auto_create

    def check_and_return(self, value: Any) -> Path:
        try:
            p = Path(value).resolve()
        except (TypeError, ValueError):
            self._failure("cannot parse value as a path", value=value)
        else:
            if self._auto_create:
                p.mkdir(parents=True, exist_ok=True)
            if not p.is_dir():
                self._failure("value is not a directory", value=value)
            return p


logging_config_iv = t.Dict({
    t.Key("level", default=LogLevel.INFO): loglevel_iv,
    t.Key("pkg-ns", default=default_pkg_ns): t.Mapping(t.String(allow_blank=True), loglevel_iv),
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
        t.Key("format", default=LogFormat.VERBOSE): logformat_iv,
    }).allow_extra("*"),
    t.Key("file", default=None): t.Null
    | t.Dict({
        t.Key("path"): DirPathTrafaret(auto_create=True),
        t.Key("filename"): t.String,
        t.Key("backup-count", default=5): t.ToInt[1:100],
        t.Key("rotation-size", default="10M"): SimpleBinarySizeTrafaret,
        t.Key("format", default=LogFormat.VERBOSE): logformat_iv,
    }).allow_extra("*"),
    t.Key("logstash", default=None): t.Null
    | t.Dict({
        t.Key("endpoint"): t.Tuple(t.String, t.Int[1:65535]),
        t.Key("protocol", default="tcp"): t.Enum("zmq.push", "zmq.pub", "tcp", "udp"),
        t.Key("ssl-enabled", default=True): t.ToBool,
        t.Key("ssl-verify", default=True): t.ToBool,
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
