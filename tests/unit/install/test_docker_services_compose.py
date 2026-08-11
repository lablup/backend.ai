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

# Services carrying the base_path parity mount: the agent and storage-proxy
# hand paths under it to the host Docker daemon, and the manager/manager-cli
# share bootstrap state (RPC keypair fixtures) through it.
PARITY_SERVICES = {"manager", "manager-cli", "agent", "storage-proxy"}

# The rest mount ONLY their own config file, read-only — they must never see
# the credentials in the other configs (e.g. the manager's DB password).
CONFIG_ONLY_SERVICES = {
    "webserver": "webserver.conf",
    "appproxy-coordinator": "app-proxy-coordinator.toml",
    "appproxy-worker": "app-proxy-worker.toml",
    "appproxy-worker-tcp": "app-proxy-worker-tcp.toml",
}

BASE_PATH = Path("/home/bai/backendai")
VERSION = "26.9.0"

KRUNNER_SHARED_PATH = "/var/lib/backend.ai/krunner"


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


def test_rendered_compose_has_all_services_with_expected_mounts(template: str) -> None:
    doc = render(template, enable_gpu=False)
    services = doc["services"]
    assert set(services.keys()) == EXPECTED_SERVICES
    assert PARITY_SERVICES | set(CONFIG_ONLY_SERVICES) == EXPECTED_SERVICES
    parity_mount = f"{BASE_PATH}:{BASE_PATH}"
    for name, service in services.items():
        assert service["image"] == service["image"].split(":")[0] + f":{VERSION}"
        assert service["image"].startswith("lablup/backend.ai-")
        assert service["network_mode"] == "host"
        assert service["working_dir"] == str(BASE_PATH)
        if name in PARITY_SERVICES:
            assert parity_mount in service["volumes"], f"{name} lacks the base_path parity mount"
        else:
            assert parity_mount not in service["volumes"], (
                f"{name} must not see the whole install directory"
            )
        if name in CLI_ONLY_SERVICES:
            assert "restart" not in service, f"{name} must not auto-restart"
        else:
            assert service["restart"] == "unless-stopped"


def test_rendered_compose_config_only_services_mount_just_their_config(template: str) -> None:
    doc = render(template, enable_gpu=False)
    services = doc["services"]
    for name, config_filename in CONFIG_ONLY_SERVICES.items():
        service = services[name]
        config_path = BASE_PATH / config_filename
        # Exactly one volume: the service's own config, read-only — nothing
        # else from the install directory (the other configs carry
        # credentials this service has no business reading).
        assert service["volumes"] == [f"{config_path}:{config_path}:ro"], name
        # The command reads the exact file that is mounted.
        assert str(config_path) in service["command"], name


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
    )
    assert rendered == "# prose mentioning the #gpu# marker stays intact\n    deploy: {}\n"
