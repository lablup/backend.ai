from __future__ import annotations

import base64

from aiohttp.test_utils import TestClient, TestServer

from ai.backend.kube.nodehelper.server import (
    TOKEN_HEADER,
    CommitRequest,
    PushRequest,
    build_app,
    commit_args,
    docker_config,
    label_args,
    push_args,
)


class TestCommitArgs:
    def test_the_container_keeps_running(self) -> None:
        args = commit_args("nerdctl", CommitRequest(container_id="c1", image="r/p/i:t"))
        assert args == [
            "nerdctl",
            "--namespace",
            "k8s.io",
            "commit",
            "--pause=false",
            "c1",
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
        async with TestClient(TestServer(build_app("/bin/false", "secret"))) as cli:
            resp = await cli.post("/v1/commit", json={"container_id": "c", "image": "i"})
            assert resp.status == 401
            resp = await cli.post(
                "/v1/commit",
                json={"container_id": "c", "image": "i"},
                headers={TOKEN_HEADER: "secret"},
            )
            assert resp.status == 500  # /bin/false fails the command
