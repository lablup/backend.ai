import etcd3
from tomlkit.items import InlineTable, Table

from ai.backend.cli.interaction import ask_host, ask_int, ask_string


def config_etcd(config_toml: dict) -> dict:
    # etcd section
    try:
        if config_toml.get("etcd") is None:
            raise KeyError
        elif type(config_toml.get("etcd")) != Table:
            raise TypeError
        etcd_config: dict = dict(config_toml["etcd"])

        etcd_namespace = ask_string(
            "Etcd name space",
            default=etcd_config["namespace"] if etcd_config.get("namespace") else "",
        )
        config_toml["etcd"]["namespace"] = etcd_namespace

        while True:
            try:
                if etcd_config.get("addr") is None:
                    raise KeyError
                elif type(etcd_config.get("addr")) != InlineTable:
                    raise TypeError
                etcd_address: dict = dict(etcd_config["addr"])
                etcd_host = ask_host("Etcd host: ", etcd_address["host"])
                if type(etcd_address.get("port")) != str:
                    etcd_port = ask_int(
                        "Etcd port",
                        default=int(etcd_address["port"]),
                        min_value=1,
                        max_value=65535,
                    )
                else:
                    raise TypeError
                if check_etcd_health(etcd_host, etcd_port):
                    break
                print("Cannot connect to etcd. Please input etcd information again.")
            except ValueError:
                print("Invalid etcd address sample.")

        etcd_user = ask_string("Etcd user name")
        etcd_password = ask_string("Etcd password")
        config_toml["etcd"]["addr"] = {"host": etcd_host, "port": etcd_port}
        config_toml["etcd"]["user"] = etcd_user
        config_toml["etcd"]["password"] = etcd_password
        return config_toml
    except ValueError:
        raise ValueError


def check_etcd_health(host: str, port: int):
    try:
        etcd_client = etcd3.Etcd3Client(host=host, port=port)
        etcd_client.close()
    except (etcd3.exceptions.ConnectionFailedError, etcd3.exceptions.ConnectionTimeoutError):
        return False
    return True
