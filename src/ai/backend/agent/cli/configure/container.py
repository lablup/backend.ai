from tomlkit.items import Table

from ai.backend.cli.interaction import ask_host, ask_number, ask_string_in_array


def config_container(config_toml: dict) -> dict:
    # container section
    try:
        if config_toml.get("container") is None:
            raise KeyError
        elif type(config_toml.get("container")) != Table:
            raise TypeError
        container_config: dict = dict(config_toml["container"])

        container_port_start = ask_number(
            "Container port range(start): ", int(container_config["port-range"][0]), 1, 65534
        )
        container_port_end = ask_number(
            "Container port range(end): ",
            int(container_config["port-range"][1]),
            container_port_start + 1,
            65534,
        )
        config_toml["container"]["port-range"] = [container_port_start, container_port_end]

        kernel_uid: int = ask_number("Kernel uid: ", int(container_config["kernel-uid"]), 1, 65535)
        kernel_gid: int = ask_number("Kernel gid: ", int(container_config["kernel-gid"]), 1, 65535)
        config_toml["container"]["kernel-uid"] = kernel_uid
        config_toml["container"]["kernel-gid"] = kernel_gid

        container_bind_host = ask_host(
            "Container bind host: ", str(container_config.get("bind-host"))
        )
        config_toml["container"]["bind-host"] = container_bind_host

        stats_type = ask_string_in_array(
            "Stats type", ["docker", "cgroup"], container_config["stats-type"]
        )
        config_toml["container"]["stats-type"] = stats_type

        sandbox_type = ask_string_in_array(
            "sandbox type", ["docker", "cgroup"], container_config["sandbox-type"]
        )
        config_toml["container"]["sandbox-type"] = sandbox_type
        return config_toml
    except ValueError:
        raise ValueError
