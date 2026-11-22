from __future__ import annotations

import asyncio
import base64
import os
import stat
from pathlib import Path
from typing import Any

import pytest
from aiohttp.test_utils import TestClient, TestServer

from ai.backend.kube.errors import NodeHelperCommandError
from ai.backend.kube.nodehelper.server import (
    MAX_CONCURRENT_COMMANDS,
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
    run_command,
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


def _hanging_command(tmp_path: Path) -> str:
    """A command that records its pid and then never ends."""
    script = tmp_path / "hang"
    script.write_text(f"#!/bin/sh\necho $$ >> {tmp_path / 'pids'}\nexec sleep 60\n")
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    return str(script)


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


class TestCommandTimeout:
    async def test_a_command_past_its_timeout_is_killed(self, tmp_path: Path) -> None:
        with pytest.raises(NodeHelperCommandError, match="timed out"):
            await run_command([_hanging_command(tmp_path)], time_limit=1.0)
        pid = int((tmp_path / "pids").read_text().split()[0])
        assert not _alive(pid)

    async def test_a_cancelled_command_is_killed(self, tmp_path: Path) -> None:
        task = asyncio.create_task(run_command([_hanging_command(tmp_path)], time_limit=60))
        for _ in range(100):
            if (tmp_path / "pids").exists():
                break
            await asyncio.sleep(0.05)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert not _alive(int((tmp_path / "pids").read_text().split()[0]))

    async def test_timed_out_commits_release_their_slots(self, tmp_path: Path) -> None:
        app = build_app(_hanging_command(tmp_path), "secret", _accept, command_timeout=1.0)
        body = {"container_id": CONTAINER_ID, "image": "i"}
        async with TestClient(TestServer(app)) as cli:
            for _ in range(MAX_CONCURRENT_COMMANDS + 1):
                resp = await cli.post("/v1/commit", json=body, headers={TOKEN_HEADER: "secret"})
                assert resp.status == 500
                assert "timed out" in (await resp.json())["error"]
