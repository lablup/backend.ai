"""Unit tests for the pure ``ag kernel`` spec builders.

The docker kernel-create path needs a live daemon and is verified via the CLI
against a running agent (see ``src/ai/backend/agent/cli/PARITY.md``). These tests
cover only the deterministic spec -> config transformation, which is what makes
the CLI's create payload faithful to the manager's.
"""

from __future__ import annotations

import uuid
from typing import Any, cast

from ai.backend.agent.cli.kernel_spec import (
    KernelCreateSpec,
    build_cluster_info,
    build_image_ref,
    build_kernel_creation_config,
    generate_cluster_ssh_keypair,
)
from ai.backend.common.docker import LabelName
from ai.backend.common.types import (
    AutoPullBehavior,
    ClusterMode,
    ImageConfig,
    SessionTypes,
)

KERNEL_ID = str(uuid.UUID("00000000-0000-0000-0000-0000000000a1"))
SESSION_ID = str(uuid.UUID("00000000-0000-0000-0000-0000000000b2"))
OWNER_ID = str(uuid.UUID("00000000-0000-0000-0000-0000000000c3"))
AGENT_ADDR = "tcp://127.0.0.1:6011"


def _image_config(**overrides: Any) -> ImageConfig:
    base: dict[str, Any] = {
        "canonical": "cr.backend.ai/stable/python:3.9-ubuntu20.04",
        "project": "stable",
        "architecture": "x86_64",
        "digest": "sha256:deadbeef",
        "repo_digest": None,
        "registry": {"name": "cr.backend.ai", "url": "", "username": None, "password": None},
        "labels": {LabelName.SERVICE_PORTS: "jupyter:http:8080"},
        "is_local": False,
        "auto_pull": AutoPullBehavior.DIGEST,
    }
    base.update(overrides)
    return cast(ImageConfig, base)


def test_minimal_spec_defaults() -> None:
    spec = KernelCreateSpec.model_validate({"image": "python:3.9"})
    assert spec.image == "python:3.9"
    assert spec.is_local is True
    assert spec.resource_slots == {"cpu": "1", "mem": str(1 * 2**30)}
    assert spec.cluster_mode is ClusterMode.SINGLE_NODE
    assert spec.session_type is SessionTypes.INTERACTIVE
    assert spec.auto_pull is AutoPullBehavior.NONE


def test_build_kernel_creation_config_has_all_keys() -> None:
    spec = KernelCreateSpec.model_validate({
        "image": "cr.backend.ai/stable/python:3.9-ubuntu20.04",
        "resource_slots": {"cpu": "2", "mem": "4294967296"},
        "resource_opts": {"shmem": "64m"},
        "scaling_group": "sg01",
    })
    image_config = _image_config()
    config = build_kernel_creation_config(
        spec,
        image_config=image_config,
        kernel_id=KERNEL_ID,
        session_id=SESSION_ID,
        owner_user_id=OWNER_ID,
        agent_addr=AGENT_ADDR,
    )

    # Every KernelCreationConfig key the manager sends must be present.
    expected_keys = {
        "image",
        "kernel_id",
        "session_id",
        "owner_user_id",
        "owner_project_id",
        "network_id",
        "auto_pull",
        "session_type",
        "cluster_mode",
        "cluster_role",
        "cluster_idx",
        "cluster_hostname",
        "local_rank",
        "uid",
        "main_gid",
        "supplementary_gids",
        "resource_slots",
        "resource_opts",
        "environ",
        "mounts",
        "package_directory",
        "idle_timeout",
        "bootstrap_script",
        "startup_command",
        "internal_data",
        "preopen_ports",
        "allocated_host_ports",
        "scaling_group",
        "agent_addr",
        "endpoint_id",
    }
    assert set(config.keys()) == expected_keys

    assert config["image"] is image_config
    assert config["kernel_id"] == KERNEL_ID
    assert config["session_id"] == SESSION_ID
    assert config["owner_user_id"] == OWNER_ID
    assert config["owner_project_id"] is None
    assert config["network_id"] == SESSION_ID
    assert config["cluster_role"] == "main"
    assert config["cluster_idx"] == 1
    assert config["cluster_hostname"] == "main1"
    assert config["local_rank"] == 0
    assert config["resource_slots"] == {"cpu": "2", "mem": "4294967296"}
    assert config["resource_opts"] == {"shmem": "64m"}
    assert config["scaling_group"] == "sg01"
    assert config["agent_addr"] == AGENT_ADDR
    assert config["package_directory"] == ()
    assert config["allocated_host_ports"] == []
    assert config["endpoint_id"] is None


def test_environ_includes_cluster_and_service_ports() -> None:
    spec = KernelCreateSpec.model_validate({"image": "img", "environ": {"MY_VAR": "1"}})
    config = build_kernel_creation_config(
        spec,
        image_config=_image_config(),
        kernel_id=KERNEL_ID,
        session_id=SESSION_ID,
        owner_user_id=OWNER_ID,
        agent_addr=AGENT_ADDR,
    )
    environ = config["environ"]
    assert environ["MY_VAR"] == "1"
    assert environ["BACKENDAI_KERNEL_ID"] == KERNEL_ID
    assert environ["BACKENDAI_KERNEL_IMAGE"] == _image_config()["canonical"]
    assert environ["BACKENDAI_CLUSTER_ROLE"] == "main"
    assert environ["BACKENDAI_CLUSTER_IDX"] == "1"
    assert environ["BACKENDAI_CLUSTER_LOCAL_RANK"] == "0"
    assert environ["BACKENDAI_CLUSTER_HOST"] == "main1"
    assert environ["BACKENDAI_SERVICE_PORTS"] == "jupyter:http:8080"


def test_environ_omits_service_ports_when_label_absent() -> None:
    spec = KernelCreateSpec.model_validate({"image": "img"})
    config = build_kernel_creation_config(
        spec,
        image_config=_image_config(labels={}),
        kernel_id=KERNEL_ID,
        session_id=SESSION_ID,
        owner_user_id=OWNER_ID,
        agent_addr=AGENT_ADDR,
    )
    assert "BACKENDAI_SERVICE_PORTS" not in config["environ"]


def test_build_cluster_info_single_node() -> None:
    spec = KernelCreateSpec.model_validate({"image": "img"})
    keypair = generate_cluster_ssh_keypair()
    cluster_info = build_cluster_info(spec, keypair)
    assert cluster_info["mode"] is ClusterMode.SINGLE_NODE
    assert cluster_info["size"] == 1
    assert cluster_info["replicas"] == {"main": 1}
    assert cluster_info["network_config"] == {}
    assert cluster_info["ssh_keypair"] is keypair
    assert cluster_info["cluster_ssh_port_mapping"] is None


def test_build_image_ref_propagates_fields() -> None:
    image_config = _image_config(is_local=True, architecture="aarch64")
    image_ref = build_image_ref(image_config)
    assert image_ref.canonical == image_config["canonical"]
    assert image_ref.architecture == "aarch64"
    assert image_ref.is_local is True


def test_generate_cluster_ssh_keypair_format() -> None:
    keypair = generate_cluster_ssh_keypair()
    assert keypair["public_key"].startswith("ssh-rsa ")
    assert keypair["public_key"].endswith("\n")
    assert "PRIVATE KEY" in keypair["private_key"]
    assert keypair["private_key"].endswith("\n")
