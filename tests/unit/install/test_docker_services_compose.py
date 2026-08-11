import importlib.resources
from pathlib import Path
from typing import Any

import pytest
from ruamel.yaml import YAML

from ai.backend.install.context import DockerContext

EXPECTED_SERVICES = {
    "manager",
    "manager-cli",
    "agent",
    "webserver",
    "storage-proxy",
    "appproxy-coordinator",
    "appproxy-worker",
    "appproxy-worker-tcp",
}

# One-off helper service: started only via `docker compose run`, never `up -d`.
CLI_ONLY_SERVICES = {"manager-cli"}

# Services on the host network: the manager and agent advertise kernel/RPC
# ports on host addresses; manager-cli is the installer's one-off tool and
# must reach halfstack at 127.0.0.1.
HOST_NET_SERVICES = {"manager", "manager-cli", "agent"}

# Services carrying the base_path parity mount: the agent and storage-proxy
# hand paths under it to the host Docker daemon; manager-cli passes fixture
# files under it to one-off commands.
PARITY_SERVICES = {"manager-cli", "agent", "storage-proxy"}

# service -> (installer-side config filename, image default-command target)
CONFIG_MOUNTS = {
    "manager": ("manager.toml", "/etc/backend.ai/manager.toml"),
    "manager-cli": ("manager.toml", "/etc/backend.ai/manager.toml"),
    "agent": ("agent.toml", "/etc/backend.ai/agent.toml"),
    "webserver": ("webserver.conf", "/etc/backend.ai/webserver.conf"),
    "storage-proxy": ("storage-proxy.toml", "/etc/backend.ai/storage-proxy.toml"),
    "appproxy-coordinator": (
        "app-proxy-coordinator.toml",
        "/etc/backend.ai/proxy-coordinator.toml",
    ),
    "appproxy-worker": ("app-proxy-worker.toml", "/etc/backend.ai/proxy-worker.toml"),
    "appproxy-worker-tcp": ("app-proxy-worker-tcp.toml", "/etc/backend.ai/proxy-worker.toml"),
}

# Bridge services publish the fixed ports of the installer's ServiceConfig
# (API ports) plus the port-proxy ranges of the bundled worker configs.
EXPECTED_PORTS = {
    "webserver": {"8090:8090"},
    "storage-proxy": {"6021:6021", "6022:6022"},
    "appproxy-coordinator": {"10200:10200"},
    "appproxy-worker": {"10201:10201", "10205-10300:10205-10300"},
    "appproxy-worker-tcp": {"10202:10202", "10501-10600:10501-10600"},
}

BASE_PATH = Path("/home/bai/backendai")
VERSION = "26.9.0"
UID = 1000
GID = 1001

KRUNNER_SHARED_PATH = "/var/lib/backend.ai/krunner"
HOST_GATEWAY_ALIAS = "host.docker.internal:host-gateway"


@pytest.fixture
def template() -> str:
    return (
        importlib.resources.files("ai.backend.install.configs")
        .joinpath("docker-compose.services.yml")
        .read_text()
    )


def render(template: str, *, enable_gpu: bool) -> dict[str, Any]:
    rendered = DockerContext.render_services_compose(
        template,
        base_path=BASE_PATH,
        version=VERSION,
        enable_gpu=enable_gpu,
        uid=UID,
        gid=GID,
    )
    assert "{{" not in rendered, "unsubstituted placeholders remain"
    doc = YAML(typ="safe").load(rendered)
    assert isinstance(doc, dict)
    return doc


def test_rendered_compose_has_dedicated_project_name(template: str) -> None:
    # The fixed project name keeps this file from sharing a compose project
    # with the halfstack compose file living in the same directory.
    doc = render(template, enable_gpu=False)
    assert doc["name"] == "backendai-services"


def test_rendered_compose_service_set_and_restart_policy(template: str) -> None:
    doc = render(template, enable_gpu=False)
    services = doc["services"]
    assert set(services.keys()) == EXPECTED_SERVICES
    for name, service in services.items():
        assert service["image"] == service["image"].split(":")[0] + f":{VERSION}"
        assert service["image"].startswith("lablup/backend.ai-")
        if name in CLI_ONLY_SERVICES:
            assert "restart" not in service, f"{name} must not auto-restart"
        else:
            assert service["restart"] == "unless-stopped"


def test_rendered_compose_networking_split(template: str) -> None:
    doc = render(template, enable_gpu=False)
    services = doc["services"]
    for name, service in services.items():
        if name in HOST_NET_SERVICES:
            assert service.get("network_mode") == "host", f"{name} must use host networking"
            assert "ports" not in service
            assert "extra_hosts" not in service
        else:
            assert "network_mode" not in service, f"{name} must stay on the bridge network"
            assert set(service["ports"]) == EXPECTED_PORTS[name], name
        # Only the webserver talks to a host-network process (the manager
        # API); everything else uses compose service DNS in the unified
        # project, so no other service needs the host-gateway alias.
        if name == "webserver":
            assert HOST_GATEWAY_ALIAS in service["extra_hosts"]
        else:
            assert "extra_hosts" not in service, name


def test_rendered_compose_includes_halfstack_as_one_project(template: str) -> None:
    doc = render(template, enable_gpu=False)
    # The halfstack file joins THIS compose project, putting every container
    # on one network (service DNS) under one `docker compose` entry file.
    assert doc["include"] == ["docker-compose.halfstack.current.yml"]
    # Startup is health-gated on the halfstack members, as in the reference
    # hand-written deployment.
    depends = {
        name: set(service.get("depends_on", {}).keys()) for name, service in doc["services"].items()
    }
    assert depends["manager"] == {
        "backendai-half-db",
        "backendai-half-redis",
        "backendai-half-etcd",
    }
    assert depends["agent"] == {"backendai-half-redis", "backendai-half-etcd"}
    assert depends["webserver"] == {"backendai-half-redis"}
    assert depends["storage-proxy"] == {"backendai-half-etcd"}
    assert depends["appproxy-coordinator"] == {"backendai-half-db", "backendai-half-redis"}
    assert depends["appproxy-worker"] == {"backendai-half-redis"}
    assert depends["appproxy-worker-tcp"] == {"backendai-half-redis"}
    # manager-cli one-offs run with --no-deps; it declares none.
    assert depends["manager-cli"] == set()
    for name, service in doc["services"].items():
        for condition in service.get("depends_on", {}).values():
            assert condition == {"condition": "service_healthy"}, name


def test_rendered_compose_config_mounts_follow_default_command_paths(template: str) -> None:
    # Every service reads its config from the image default-command path via
    # a per-file read-only mount — same convention as a hand-written compose
    # deployment, with no `command:`/`working_dir` overrides (manager-cli, the
    # installer's own tool, is the deliberate exception).
    doc = render(template, enable_gpu=False)
    services = doc["services"]
    for name, (config_filename, target) in CONFIG_MOUNTS.items():
        service = services[name]
        expected = f"{BASE_PATH / config_filename}:{target}:ro"
        assert expected in service["volumes"], f"{name} lacks the config mount {expected}"
        if name not in CLI_ONLY_SERVICES:
            assert "command" not in service, f"{name} must run the image default command"
            assert "working_dir" not in service


def test_rendered_compose_parity_mounts(template: str) -> None:
    doc = render(template, enable_gpu=False)
    services = doc["services"]
    parity_mount = f"{BASE_PATH}:{BASE_PATH}"
    for name, service in services.items():
        if name in PARITY_SERVICES:
            assert parity_mount in service["volumes"], f"{name} lacks the base_path parity mount"
        else:
            assert parity_mount not in service["volumes"], (
                f"{name} must not mount the whole install directory"
            )
    # The manager exchanges the RPC keypair through the fixtures directory,
    # where both its entrypoint and `mgr generate-rpc-keypair` place it.
    assert f"{BASE_PATH}/fixtures:/app/fixtures" in services["manager"]["volumes"]


def test_rendered_compose_elevated_services(template: str) -> None:
    doc = render(template, enable_gpu=False)
    services = doc["services"]
    docker_sock = "/var/run/docker.sock:/var/run/docker.sock"
    for name in ("manager", "agent"):
        assert services[name]["privileged"] is True
        assert docker_sock in services[name]["volumes"]
    agent = services["agent"]
    assert agent["pid"] == "host"
    assert agent["cgroup"] == "host"
    krunner_mount = f"{KRUNNER_SHARED_PATH}:{KRUNNER_SHARED_PATH}"
    assert krunner_mount in agent["volumes"]
    assert str(DockerContext.KRUNNER_SHARED_PATH) == KRUNNER_SHARED_PATH
    # the GPU reservation stays commented out without a CUDA accelerator
    assert "deploy" not in agent


def test_rendered_compose_storage_proxy_runs_as_installing_user(template: str) -> None:
    doc = render(template, enable_gpu=False)
    storage = doc["services"]["storage-proxy"]
    assert storage["user"] == f"{UID}:{GID}"
    # no other service overrides its user
    for name, service in doc["services"].items():
        if name != "storage-proxy":
            assert "user" not in service, name


def test_rendered_compose_manager_cli_is_unprivileged_one_off(template: str) -> None:
    doc = render(template, enable_gpu=False)
    services = doc["services"]
    manager_cli = services["manager-cli"]
    # Same image as the manager, but no privileges and no docker socket.
    assert manager_cli["image"] == services["manager"]["image"]
    assert "privileged" not in manager_cli
    assert not any("docker.sock" in volume for volume in manager_cli["volumes"])
    # The "cli" profile keeps `docker compose up -d` from starting it, while
    # `docker compose run manager-cli ...` still works (run ignores profile
    # gating for the explicitly named service).
    assert manager_cli["profiles"] == ["cli"]
    assert manager_cli["command"] == ["true"]
    # One-off CLI invocations use install-directory-relative paths
    # (e.g. `mgr generate-rpc-keypair fixtures/manager`).
    assert manager_cli["working_dir"] == str(BASE_PATH)


def test_rendered_compose_gpu_enabled(template: str) -> None:
    doc = render(template, enable_gpu=True)
    agent = doc["services"]["agent"]
    devices = agent["deploy"]["resources"]["reservations"]["devices"]
    assert devices == [{"driver": "nvidia", "count": "all", "capabilities": ["gpu"]}]
    # only the agent gains the GPU reservation
    for name, service in doc["services"].items():
        if name != "agent":
            assert "deploy" not in service


def test_gpu_marker_strip_is_line_anchored() -> None:
    synthetic = "# prose mentioning the #gpu# marker stays intact\n#gpu#    deploy: {}\n"
    rendered = DockerContext.render_services_compose(
        synthetic,
        base_path=BASE_PATH,
        version=VERSION,
        enable_gpu=True,
        uid=UID,
        gid=GID,
    )
    assert rendered == "# prose mentioning the #gpu# marker stays intact\n    deploy: {}\n"
