from __future__ import annotations

import json
from dataclasses import replace
from typing import Any, cast
from uuid import UUID

import pytest

from ai.backend.common.kernel_creation_config import KernelCreationConfig
from ai.backend.common.types import ClusterInfo, ClusterMode, SessionId
from ai.backend.kube.crd.session import SessionWorkload
from ai.backend.manager.clients.compute_cluster.mapping import (
    SessionGroupSpec,
    SessionPlacement,
    build_session_objects,
    queue_name,
)

SESSION_ID = SessionId(UUID("22222222-0000-0000-0000-000000000001"))


def _config(kernel_id: str, *, username: str | None = None) -> KernelCreationConfig:
    raw: dict[str, Any] = {
        "image": {
            "canonical": "cr.backend.ai/stable/python:3.13",
            "project": "stable",
            "architecture": "x86_64",
            "digest": "sha256:abc",
            "repo_digest": None,
            "registry": {
                "name": "cr.backend.ai",
                "url": "https://cr.backend.ai",
                "username": username,
                "password": "pw" if username else None,
            },
            "labels": {"ai.backend.base-distro": "ubuntu22.04"},
            "is_local": False,
            "auto_pull": "digest",
        },
        "kernel_id": kernel_id,
        "session_id": str(SESSION_ID),
        "session_name": "s",
        "owner_user_id": "u",
        "owner_project_id": None,
        "network_id": str(SESSION_ID),
        "auto_pull": "digest",
        "session_type": "interactive",
        "cluster_mode": "single-node",
        "cluster_role": "main",
        "cluster_idx": 1,
        "cluster_hostname": "main1",
        "local_rank": 0,
        "uid": None,
        "main_gid": None,
        "supplementary_gids": [],
        "resource_slots": {"cpu": "1", "mem": "1073741824"},
        "resource_opts": {},
        "environ": {"BACKENDAI_KERNEL_ID": kernel_id},
        "mounts": [],
        "package_directory": [],
        "idle_timeout": 600,
        "bootstrap_script": "echo hi",
        "startup_command": None,
        "internal_data": {"dotfiles": []},
        "preopen_ports": [],
        "allocated_host_ports": [],
        "scaling_group": "k8s",
        "agent_addr": "",
        "endpoint_id": None,
    }
    return cast(KernelCreationConfig, raw)


@pytest.fixture
def placement() -> SessionPlacement:
    return SessionPlacement(
        namespace="bai-p1",
        session_id=SESSION_ID,
        session_name="s",
        session_type="interactive",
        owner_user_id="u",
        owner_project_id="p1",
        access_key="AKIA",
        domain_name="default",
        resource_group="k8s",
        queue="k8s.p1",
        priority=10,
        network_id=None,
    )


@pytest.fixture
def cluster_info() -> ClusterInfo:
    return ClusterInfo(
        mode=ClusterMode.SINGLE_NODE,
        size=1,
        replicas={"main": 1},
        network_config={"mode": "kubernetes"},
        ssh_keypair={"public_key": "pub", "private_key": "priv"},
        cluster_ssh_port_mapping=None,
    )


class TestBuildSessionObjects:
    def test_workload_is_a_valid_session_workload(
        self, placement: SessionPlacement, cluster_info: ClusterInfo
    ) -> None:
        objects = build_session_objects(placement, [_config("k1")], cluster_info)
        workload = SessionWorkload.model_validate(objects.workload)
        assert workload.metadata["name"] == f"s-{SESSION_ID}"
        assert workload.spec.scheduler_name == "sokovan"
        assert workload.spec.queue == "k8s.p1"
        assert workload.spec.kernels[0].resource_slots == {"cpu": "1", "mem": "1073741824"}

    def test_secrets_stay_out_of_the_workload(
        self, placement: SessionPlacement, cluster_info: ClusterInfo
    ) -> None:
        objects = build_session_objects(placement, [_config("k1")], cluster_info)
        assert "internalData" not in json.dumps(objects.workload)
        data = objects.secret["stringData"]
        assert json.loads(data["cluster-ssh-keypair"])["private_key"] == "priv"
        assert json.loads(data["kernel-k1"])["bootstrap_script"] == "echo hi"

    def test_registry_credentials_become_a_pull_secret(
        self, placement: SessionPlacement, cluster_info: ClusterInfo
    ) -> None:
        objects = build_session_objects(placement, [_config("k1", username="bot")], cluster_info)
        assert objects.pull_secret is not None
        auths = json.loads(objects.pull_secret["stringData"][".dockerconfigjson"])["auths"]
        assert set(auths) == {"cr.backend.ai"}
        kernel = SessionWorkload.model_validate(objects.workload).spec.kernels[0]
        assert kernel.image.pull_secret_name == objects.pull_secret["metadata"]["name"]

    def test_public_registry_needs_no_pull_secret(
        self, placement: SessionPlacement, cluster_info: ClusterInfo
    ) -> None:
        objects = build_session_objects(placement, [_config("k1")], cluster_info)
        assert objects.pull_secret is None

    def test_a_session_without_a_group_has_no_session_group(
        self, placement: SessionPlacement, cluster_info: ClusterInfo
    ) -> None:
        objects = build_session_objects(placement, [_config("k1")], cluster_info)
        assert "sessionGroup" not in objects.workload["spec"]

    def test_an_all_or_none_group_carries_its_member_count(
        self, placement: SessionPlacement, cluster_info: ClusterInfo
    ) -> None:
        group = SessionGroupSpec(
            id="33333333-0000-0000-0000-000000000001",
            direction="spread",
            enforcement="strict",
            admission="all_or_none",
            member_count=3,
        )
        objects = build_session_objects(
            replace(placement, session_group=group), [_config("k1")], cluster_info
        )
        assert objects.workload["spec"]["sessionGroup"] == {
            "id": "33333333-0000-0000-0000-000000000001",
            "direction": "spread",
            "enforcement": "strict",
            "admission": "all_or_none",
            "memberCount": 3,
        }

    def test_an_independent_group_has_no_member_count(
        self, placement: SessionPlacement, cluster_info: ClusterInfo
    ) -> None:
        group = SessionGroupSpec(
            id="33333333-0000-0000-0000-000000000002",
            direction="pack",
            enforcement="preferred",
            admission="independent",
            member_count=None,
        )
        objects = build_session_objects(
            replace(placement, session_group=group), [_config("k1")], cluster_info
        )
        assert "memberCount" not in objects.workload["spec"]["sessionGroup"]

    def test_vfolder_mounts_carry_the_storage_proxy_path(
        self, placement: SessionPlacement, cluster_info: ClusterInfo
    ) -> None:
        config = _config("k1")
        config["mounts"] = [
            {
                "name": "data",
                "vfid": "q:abc",
                "vfsubpath": ".",
                "host_path": "/vfroot/nfs/q/ab/c",
                "kernel_path": "/home/work/data",
                "mount_perm": "ro",
                "usage_mode": "general",
            }
        ]
        objects = build_session_objects(placement, [config], cluster_info)
        [mount] = SessionWorkload.model_validate(objects.workload).spec.kernels[0].mounts
        assert (mount.host_path, mount.kernel_path, mount.mount_perm) == (
            "/vfroot/nfs/q/ab/c",
            "/home/work/data",
            "ro",
        )


class TestQueueName:
    def test_a_valid_name_is_kept(self) -> None:
        assert queue_name("default") == "default"

    def test_project_queue_sits_under_the_group_queue(self) -> None:
        project = UUID("33333333-0000-0000-0000-000000000001")
        assert queue_name("default", project) == f"default.{project}"

    def test_names_that_normalize_alike_stay_distinct(self) -> None:
        names = {queue_name(name) for name in ("rg-a", "rg_a", "RG-A", "rg.a")}
        assert len(names) == 4

    def test_a_normalized_name_is_stable(self) -> None:
        assert queue_name("rg_a") == queue_name("rg_a")
        assert queue_name("rg_a").startswith("rg-a-")
