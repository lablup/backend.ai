import os
from typing import Optional

from ai.backend.cli.interaction import ask_string_in_array, ask_string, ask_number, ask_host, ask_path
from tomlkit.items import Table, InlineTable


def config_manager(config_toml: dict) -> dict:
    # manager section
    try:
        if config_toml.get("manager") is None:
            raise KeyError
        elif type(config_toml.get("manager")) != Table:
            raise TypeError
        manager_config: dict = dict(config_toml["manager"])
        cpu_count: Optional[int] = os.cpu_count()
        if cpu_count:
            no_of_processors: int = ask_number("How many processors that manager uses: ", 1, 1,
                                               cpu_count)
            config_toml["manager"]["num-proc"] = no_of_processors

        secret_token: str = ask_string("Secret token", use_default=False)
        if secret_token:
            config_toml["manager"]["secret"] = secret_token
        else:
            config_toml["manager"].pop("secret")

        daemon_user: str = ask_string("User name used for the manager daemon", use_default=False)
        daemon_group: str = ask_string("Group name used for the manager daemon", use_default=False)
        if daemon_user:
            config_toml["manager"]["user"] = daemon_user
        else:
            config_toml["manager"].pop("user")
        if daemon_group:
            config_toml["manager"]["group"] = daemon_group
        else:
            config_toml["manager"].pop("group")

        try:
            if manager_config.get("service-addr") is None:
                raise KeyError
            elif type(manager_config.get("service-addr")) != InlineTable:
                raise TypeError
            manager_address: dict = dict(manager_config["service-addr"])
            manager_host = ask_host("Manager host: ", manager_address["host"])
            if type(manager_address.get("port")) != str:
                manager_port = ask_number("Manager port: ", int(manager_address["port"]), 1, 65535)
            else:
                raise TypeError
            config_toml["manager"]["service-addr"] = {"host": manager_host, "port": manager_port}
        except ValueError:
            raise ValueError

        ssl_enabled = ask_string_in_array("Enable SSL", ["true", "false"], "false")
        config_toml["manager"]["ssl-enabled"] = ssl_enabled == "true"

        if ssl_enabled == "true":
            ssl_cert = ask_path("SSL cert path")
            ssl_private_key = ask_path("SSL private key path")
            config_toml["manager"]["ssl-cert"] = ssl_cert
            config_toml["manager"]["ssl-privkey"] = ssl_private_key
        else:
            config_toml["manager"].pop("ssl-cert")
            config_toml["manager"].pop("ssl-privkey")
        while True:
            try:
                heartbeat_timeout = float(input("Heartbeat timeout: "))
                config_toml["manager"]["heartbeat-timeout"] = heartbeat_timeout
                break
            except ValueError:
                print("Please input correct heartbeat timeout value as float.")

        node_name = ask_string("Manager node name", use_default=False)
        if node_name:
            config_toml["manager"]["id"] = node_name
        else:
            config_toml["manager"].pop("id")

        pid_path = ask_string("PID file path", use_default=False)
        if pid_path == "":
            config_toml["manager"].pop("pid-file")
        elif pid_path and os.path.exists(pid_path):
            config_toml["manager"]["pid-file"] = pid_path

        hide_agent = ask_string_in_array("Hide agent and container ID", ["true", "false"],
                                         config_toml["manager"]["hide-agents"])
        config_toml["manager"]["hide-agents"] = hide_agent == "true"

        event_loop = ask_string_in_array("Event loop", ["asyncio", "uvloop", ""], "")
        if event_loop:
            config_toml["manager"]["event-loop"] = event_loop
        else:
            config_toml["manager"].pop("event-loop")
        config_toml["manager"].pop("importer-image")
        return config_toml
    except ValueError:
        raise ValueError
