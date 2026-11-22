from __future__ import annotations

import base64
from typing import Any

import pytest
from aiohttp.test_utils import TestClient, TestServer

from ai.backend.kube.errors import NodeHelperCommandError
from ai.backend.kube.nodehelper.server import (
    TOKEN_HEADER,
    CommitRequest,
    PushRequest,
    build_app,
    check_kernel_pod,
    commit_args,
    cri_labels,
    docker_config,
    label_args,
    push_args,
)

CONTAINER_ID = "0123456789abcdef"


async def _accept(container_id: str) -> None:
    return None


async def _refuse(container_id: str) -> None:
    raise NodeHelperCommandError("not a kernel container")


class TestCommitArgs:
    def test_the_container_keeps_running(self) -> None:
        args = commit_args("nerdctl", CommitRequest(container_id=CONTAINER_ID, image="r/p/i:t"))
        assert args == [
            "nerdctl",
            "--namespace",
            "k8s.io",
            "commit",
            "--pause=false",
            CONTAINER_ID,
            "r/p/i:t",
        ]


class TestLabelArgs:
    def test_labels_are_added_in_the_registry(self) -> None:
        args = label_args("crane", "r/p/i:t", {"b": "2", "a": "1"}, insecure=True)
        assert args == [
            "crane",
            "mutate",
            "--insecure",
            "--label",
            "a=1",
            "--label",
            "b=2",
            "r/p/i:t",
        ]


class TestPushArgs:
    def test_insecure_registry(self) -> None:
        args = push_args("nerdctl", PushRequest(image="r:5000/p/i:t", insecure=True))
        assert "--insecure-registry" in args and args[-2:] == ["push", "r:5000/p/i:t"]

    def test_credentials_go_to_the_docker_config_of_the_registry(self) -> None:
        config = docker_config(PushRequest(image="r:5000/p/i:t", username="u", password="p"))
        assert config == {"auths": {"r:5000": {"auth": base64.b64encode(b"u:p").decode()}}}


class TestToken:
    async def test_a_request_without_the_token_is_refused(self) -> None:
        body = {"container_id": CONTAINER_ID, "image": "i"}
        async with TestClient(TestServer(build_app("/bin/false", "secret", _accept))) as cli:
            resp = await cli.post("/v1/commit", json=body)
            assert resp.status == 401
            resp = await cli.post("/v1/commit", json=body, headers={TOKEN_HEADER: "secret"})
            assert resp.status == 500  # /bin/false fails the command


class TestCommitRequest:
    async def test_a_container_that_is_not_a_kernel_is_refused(self) -> None:
        body = {"container_id": CONTAINER_ID, "image": "i"}
        async with TestClient(TestServer(build_app("/bin/true", "secret", _refuse))) as cli:
            resp = await cli.post("/v1/commit", json=body, headers={TOKEN_HEADER: "secret"})
            assert resp.status == 403

    @pytest.mark.parametrize(
        "body",
        [{"container_id": "--rm", "image": "i"}, {"container_id": CONTAINER_ID, "image": "-x"}],
        ids=["option-as-container", "option-as-image"],
    )
    async def test_arguments_that_look_like_options_are_refused(self, body: dict[str, str]) -> None:
        async with TestClient(TestServer(build_app("/bin/true", "secret", _accept))) as cli:
            resp = await cli.post("/v1/commit", json=body, headers={TOKEN_HEADER: "secret"})
            assert resp.status == 400


def _kernel_pod(**overrides: Any) -> dict[str, Any]:
    pod: dict[str, Any] = {
        "metadata": {"labels": {"app.kubernetes.io/managed-by": "backendai-session-controller"}},
        "spec": {"nodeName": "n1"},
        "status": {
            "containerStatuses": [{"name": "kernel", "containerID": f"containerd://{CONTAINER_ID}"}]
        },
    }
    pod.update(overrides)
    return pod


class TestCheckKernelPod:
    def test_the_kernel_container_of_a_session_pod_on_this_node_passes(self) -> None:
        check_kernel_pod(_kernel_pod(), CONTAINER_ID, "n1")

    @pytest.mark.parametrize(
        ("pod", "node"),
        [
            (_kernel_pod(metadata={"labels": {}}), "n1"),
            (_kernel_pod(), "n2"),
            (_kernel_pod(status={"containerStatuses": []}), "n1"),
        ],
        ids=["foreign-pod", "other-node", "other-container"],
    )
    def test_anything_else_is_refused(self, pod: dict[str, Any], node: str) -> None:
        with pytest.raises(NodeHelperCommandError):
            check_kernel_pod(pod, CONTAINER_ID, node)


class TestCriLabels:
    def test_labels_of_a_native_inspection(self) -> None:
        assert cri_labels([{"Labels": {"io.kubernetes.pod.name": "p"}}]) == {
            "io.kubernetes.pod.name": "p"
        }
