import asyncio
from typing import Optional, cast

import async_timeout
import grpc
from etcetra.types import HostPortPair as EtcetraHostPortPair
from tomlkit.items import InlineTable, Table
from tomlkit.toml_document import TOMLDocument

from ai.backend.cli.interaction import ask_host, ask_port, ask_string
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes


default_etcd_scope_prefix_map = {
    ConfigScopes.GLOBAL: "",
}


def config_etcd(config_toml: TOMLDocument) -> TOMLDocument:
    try:
        if config_toml.get("etcd") is None:
            raise KeyError
        elif type(config_toml.get("etcd")) != Table:
            raise TypeError
        # The type-anno in tomlkit's Table.unwrap() method is wrong...
        template = cast(dict, config_toml["etcd"].unwrap())

        while True:
            try:
                if template.get("addr") is None:
                    raise KeyError
                elif type(template.get("addr")) != InlineTable:
                    raise TypeError
                etcd_addr = template["addr"]
                etcd_host = ask_host("etcd host", etcd_addr["host"])
                if type(etcd_addr.get("port")) != str:
                    etcd_port = ask_port("etcd port", default=int(etcd_addr["port"]))
                else:
                    raise TypeError

                etcd_user = ask_string("etcd username", allow_empty=True)
                etcd_password = ask_string("etcd password", allow_empty=True)
                if check_etcd_health(etcd_host, etcd_port, etcd_user, etcd_password):
                    break
                print("Cannot connect to etcd. Please input etcd information again.")
            except ValueError:
                print("Invalid etcd address sample.")

        config_toml["etcd"]["addr"] = {"host": etcd_host, "port": etcd_port}
        config_toml["etcd"]["user"] = etcd_user
        config_toml["etcd"]["password"] = etcd_password
        return config_toml
    except ValueError:
        raise ValueError


def check_etcd_health(
    host: str,
    port: int,
    etcd_user: Optional[str],
    etcd_password: Optional[str],
) -> bool:
    return asyncio.run(_check_etcd_health(host, port, etcd_user, etcd_password))


async def _check_etcd_health(
    host: str,
    port: int,
    etcd_user: Optional[str],
    etcd_password: Optional[str],
) -> bool:
    if etcd_user:
        etcd_client = AsyncEtcd(
            EtcetraHostPortPair(host, port),
            namespace="local",
            scope_prefix_map=default_etcd_scope_prefix_map,
            credentials={
                "user": etcd_user,
                "password": etcd_password,
            },
        )
    else:
        etcd_client = AsyncEtcd(
            EtcetraHostPortPair(host, port),
            namespace="local",
            scope_prefix_map=default_etcd_scope_prefix_map,
        )
    try:
        with async_timeout.timeout(5.0):
            await etcd_client.put("ping", "hello")
            value = await etcd_client.get("ping")
        if value is not None and value == "hello":
            return True
    except (grpc.RpcError, IOError, asyncio.TimeoutError):
        # FIXME: replace grpc error with etcetra error
        print(f"Could not connect to the etcd at {host}:{port}!")
        return False
    print(f"Did not get the correct reply from the etcd at {host}:{port}!")
    return False
