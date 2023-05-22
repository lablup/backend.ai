import os
import sys
from pathlib import Path
from pprint import pformat
from typing import Any

import click
import trafaret as t

from ai.backend.common import config
from ai.backend.common import validators as tx

datastore_local_config = (
    t.Dict(
        {
            t.Key("datastore"): t.Dict(
                {
                    t.Key("rpc-listen-addr", default=("", 6001)): tx.HostPortPair(
                        allow_blank_host=True
                    ),
                    t.Key("id", default=None): t.Null | t.String,
                    t.Key("pid-file", default=os.devnull): tx.Path(
                        type="file", allow_nonexisting=True, allow_devnull=True
                    ),
                    t.Key("event-loop", default="asyncio"): t.Enum("asyncio", "uvloop"),
                    t.Key("aiomonitor-port", default=48400): t.ToInt[1:65535],
                }
            ).allow_extra("*"),
            t.Key("debug"): t.Dict(
                {
                    t.Key("enabled", default=False): t.ToBool,
                    t.Key("asyncio", default=False): t.ToBool,
                    t.Key("enhanced-aiomonitor-task-info", default=False): t.ToBool,
                }
            ).allow_extra("*"),
        }
    )
    .merge(config.etcd_config_iv)
    .allow_extra("*")
)


def load(config_path: Path | None = None) -> dict[str, Any]:
    raw_cfg, cfg_src_path = config.read_from_file(config_path, "datastore")

    try:
        cfg = config.check(raw_cfg, datastore_local_config)
        if "debug" in cfg and cfg["debug"]["enabled"]:
            print("== Datastore configuration ==", file=sys.stderr)
            print(pformat(cfg), file=sys.stderr)
        cfg["_src"] = cfg_src_path
    except config.ConfigurationError as e:
        print("Validation of datastore configuration has failed:", file=sys.stderr)
        print(pformat(e.invalid_data), file=sys.stderr)
        raise click.Abort()
    else:
        return cfg


pool_connect_opts: dict[str, Any] = {
    "statement_cache_size": 0,
    # "server_settings": {
    #     "prepared_statement_name_func": (
    #         lambda: f"__asyncpg_{uuid.uuid4()}__"
    #     ),  # https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#prepared-statement-name
    # }
}
