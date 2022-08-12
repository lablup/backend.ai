from tomlkit.items import InlineTable, Table

from ai.backend.cli.interaction import ask_choice, ask_host, ask_int, ask_path


def config_watcher(config_toml: dict) -> dict:
    # watcher section
    try:
        if config_toml.get("watcher") is None:
            raise KeyError
        elif type(config_toml.get("watcher")) != Table:
            raise TypeError
        watcher_config: dict = dict(config_toml["watcher"])

        try:
            if watcher_config.get("service-addr") is None:
                raise KeyError
            elif type(watcher_config.get("service-addr")) != InlineTable:
                raise TypeError
            watcher_address: dict = dict(watcher_config["service-addr"])
            watcher_host = ask_host("Watcher host: ", watcher_address["host"])
            if type(watcher_address.get("port")) != str:
                watcher_port = ask_int(
                    "watcher port",
                    default=int(watcher_address["port"]),
                    min_value=1,
                    max_value=65535,
                )
            else:
                raise TypeError
            config_toml["watcher"]["service-addr"] = {"host": watcher_host, "port": watcher_port}
        except ValueError:
            raise ValueError

        ssl_enabled = ask_choice("Enable SSL", ["true", "false"], default="false")
        config_toml["watcher"]["ssl-enabled"] = ssl_enabled == "true"
        if ssl_enabled == "true":
            ssl_cert = ask_path("SSL cert path")
            ssl_private_key = ask_path("SSL private key path")
            config_toml["watcher"]["ssl-cert"] = ssl_cert
            config_toml["watcher"]["ssl-key"] = ssl_private_key
        else:
            config_toml["watcher"].pop("ssl-cert")
            config_toml["watcher"].pop("ssl-key")
        return config_toml
    except ValueError:
        raise ValueError
