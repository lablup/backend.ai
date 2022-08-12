import os

from tomlkit.items import InlineTable, Table

from ai.backend.cli.interaction import ask_host, ask_port, ask_string, ask_choice


def config_agent(config_toml: dict) -> dict:
    # agent section
    try:
        # TODO: pre-populate existing values as placeholder text using readline
        # TODO: eliminate use of toml.InlineTable
        if config_toml.get("agent") is None:
            raise KeyError
        elif type(config_toml.get("agent")) != Table:
            raise TypeError
        agent_config = dict(config_toml["agent"])

        agent_mode = ask_choice("Agent mode", ["docker", "kubernetes"], "docker")
        config_toml["agent"]["mode"] = agent_mode

        try:
            if agent_config.get("rpc-listen-addr") is None:
                raise KeyError
            elif type(agent_config.get("rpc-listen-addr")) != InlineTable:
                raise TypeError
            agent_rpc_address = dict(agent_config["rpc-listen-addr"])
            agent_rpc_host = ask_host("The IP to bind the Agent RPC service", "127.0.0.1")
            if type(agent_rpc_address.get("port")) != str:
                agent_rpc_port = ask_port(
                    "Agent RPC listening port", default=int(agent_rpc_address["port"])
                )
            else:
                raise TypeError
            config_toml["agent"]["rpc-listen-addr"] = {
                "host": agent_rpc_host,
                "port": agent_rpc_port,
            }
        except ValueError:
            raise ValueError

        agent_socket_port = ask_port(
            "Agent socket port", default=int(agent_config["agent-sock-port"])
        )
        config_toml["agent"]["agent-sock-port"] = agent_socket_port

        node_name = ask_string("Agent node name")
        if node_name:
            config_toml["agent"]["id"] = node_name
        else:
            config_toml["agent"].pop("id")

        scaling_group = ask_string("Scaling group", default=agent_config["scaling-group"])
        config_toml["agent"]["scaling-group"] = scaling_group

        pid_path = ask_string("PID file path")
        if pid_path == "":
            config_toml["agent"].pop("pid-file")
        elif pid_path and os.path.exists(pid_path):
            config_toml["agent"]["pid-file"] = pid_path

        event_loop = ask_choice("Event loop", ["asyncio", "uvloop", ""], "")
        if event_loop:
            config_toml["agent"]["event-loop"] = event_loop
        else:
            config_toml["agent"].pop("event-loop")

        skip_manager_detection = ask_choice("Skip manager detection", ["true", "false", ""], "")
        if skip_manager_detection:
            config_toml["agent"]["skip-manager-detection"] = skip_manager_detection
        else:
            config_toml["agent"].pop("skip-manager-detection")
        return config_toml
    except ValueError:
        raise ValueError
