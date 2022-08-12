from tomlkit.items import Table

from ai.backend.cli.interaction import ask_choice, ask_host, ask_int, ask_port


def config_container(config_toml: dict) -> dict:
    # container section
    try:
        if config_toml.get("container") is None:
            raise KeyError
        elif type(config_toml.get("container")) != Table:
            raise TypeError
        container_config: dict = dict(config_toml["container"])

        container_port_start = ask_int(
            "Container port range (begin, inclusivel)",
            default=int(container_config["port-range"][0]),
            min_value=1,
            max_value=65534,
        )
        container_port_end = ask_int(
            "Container port range (end, inclusive)",
            default=int(container_config["port-range"][1]),
            min_value=container_port_start + 1,
            max_value=65534,
        )
        config_toml["container"]["port-range"] = [container_port_start, container_port_end]

        kernel_uid: int = ask_port(
            "UID for user containers", default=int(container_config["kernel-uid"])
        )
        kernel_gid: int = ask_port(
            "GID for user containers", default=int(container_config["kernel-gid"])
        )
        config_toml["container"]["kernel-uid"] = kernel_uid
        config_toml["container"]["kernel-gid"] = kernel_gid

        container_bind_host = ask_host(
            "Container bind host: ", str(container_config.get("bind-host"))
        )
        config_toml["container"]["bind-host"] = container_bind_host

        stats_type = ask_choice(
            "Stats type",
            ["docker", "cgroup"],
            default=container_config["stats-type"],
        )
        config_toml["container"]["stats-type"] = stats_type

        sandbox_type = ask_choice(
            "sandbox type",
            ["docker", "cgroup"],
            default=container_config["sandbox-type"],
        )
        config_toml["container"]["sandbox-type"] = sandbox_type
        return config_toml
    except ValueError:
        raise ValueError
