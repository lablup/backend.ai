import importlib.resources
from pathlib import Path
from typing import Any

import pytest
from ruamel.yaml import YAML

from ai.backend.install.context import DockerContext

EXPECTED_SERVICES = {
    "manager",
    "agent",
    "webserver",
    "storage-proxy",
    "appproxy-coordinator",
    "appproxy-worker",
    "appproxy-worker-tcp",
}

BASE_PATH = Path("/home/bai/backendai")
VERSION = "26.9.0"


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


def test_rendered_compose_has_all_services_with_parity_mounts(template: str) -> None:
    doc = render(template, enable_gpu=False)
    services = doc["services"]
    assert set(services.keys()) == EXPECTED_SERVICES
    parity_mount = f"{BASE_PATH}:{BASE_PATH}"
    for name, service in services.items():
        assert service["image"] == service["image"].split(":")[0] + f":{VERSION}"
        assert service["image"].startswith("lablup/backend.ai-")
        assert service["network_mode"] == "host"
        assert service["working_dir"] == str(BASE_PATH)
        assert parity_mount in service["volumes"], f"{name} lacks the base_path parity mount"
        assert service["restart"] == "unless-stopped"


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
    krunner_mount = "/tmp/backend-ai-krunner:/tmp/backend-ai-krunner"
    assert krunner_mount in agent["volumes"]
    # the GPU reservation stays commented out without a CUDA accelerator
    assert "deploy" not in agent


def test_rendered_compose_gpu_enabled(template: str) -> None:
    doc = render(template, enable_gpu=True)
    agent = doc["services"]["agent"]
    devices = agent["deploy"]["resources"]["reservations"]["devices"]
    assert devices == [{"driver": "nvidia", "count": "all", "capabilities": ["gpu"]}]
    # only the agent gains the GPU reservation
    for name, service in doc["services"].items():
        if name != "agent":
            assert "deploy" not in service
