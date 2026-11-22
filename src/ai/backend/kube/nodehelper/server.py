"""node helper: what the Agent did with the container engine of its node and a Pod cannot,
here a session commit and its push (suggestion-1122 9.2). One per node, beside containerd.

`nerdctl` works on the CRI namespace (`k8s.io`), where the kubelet's containers live. It has no
LABEL change for a commit, so the labels go onto the pushed image in the registry (`crane`).
The helper keeps no state between requests: a push carries the labels of its commit.
"""

from __future__ import annotations

import asyncio
import base64
import hmac
import json
import logging
import re
import tempfile
from collections.abc import Awaitable, Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, Final

from aiohttp import web
from aiohttp.typedefs import Handler
from kubernetes_asyncio import client
from kubernetes_asyncio.client.exceptions import ApiException
from pydantic import BaseModel, Field, ValidationError, field_validator

from ai.backend.kube.controller.naming import KERNEL_CONTAINER, LABEL_MANAGED_BY, MANAGED_BY
from ai.backend.kube.errors import NodeHelperCommandError
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

CRI_NAMESPACE: Final = "k8s.io"
TOKEN_HEADER: Final = "X-BackendAI-Node-Helper-Token"
NODE_HELPER_TOKEN_ENV: Final = "BACKENDAI_NODE_HELPER_TOKEN"
# CRI labels the kubelet puts on every container
CRI_POD_NAMESPACE: Final = "io.kubernetes.pod.namespace"
CRI_POD_NAME: Final = "io.kubernetes.pod.name"
CRI_CONTAINER_NAME: Final = "io.kubernetes.container.name"
MAX_CONCURRENT_COMMANDS: Final = 2
_RX_CONTAINER_ID: Final = re.compile(r"^[0-9a-f]{12,64}$")
_RX_IMAGE: Final = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@-]*$")


def _check_image(value: str) -> str:
    if not _RX_IMAGE.match(value):
        raise ValueError("invalid image reference")
    return value


class CommitRequest(BaseModel):
    container_id: str
    image: str = Field(description="Canonical name the commit is tagged with")

    @field_validator("container_id")
    @classmethod
    def _container_id(cls, value: str) -> str:
        if not _RX_CONTAINER_ID.match(value):
            raise ValueError("invalid container id")
        return value

    @field_validator("image")
    @classmethod
    def _image(cls, value: str) -> str:
        return _check_image(value)


class PushRequest(BaseModel):
    image: str
    username: str | None = None
    password: str | None = None
    insecure: bool = False
    labels: dict[str, str] = Field(default_factory=dict, description="Labels of the commit")

    @field_validator("image")
    @classmethod
    def _image(cls, value: str) -> str:
        return _check_image(value)


type ContainerVerifier = Callable[[str], Awaitable[None]]


def commit_args(nerdctl: str, req: CommitRequest) -> list[str]:
    """The container keeps running, as with the Docker Agent."""
    return [
        nerdctl,
        "--namespace",
        CRI_NAMESPACE,
        "commit",
        "--pause=false",
        req.container_id,
        req.image,
    ]


def inspect_args(nerdctl: str, container_id: str) -> list[str]:
    return [nerdctl, "--namespace", CRI_NAMESPACE, "inspect", "--mode=native", container_id]


def label_args(crane: str, image: str, labels: Mapping[str, str], insecure: bool) -> list[str]:
    """Add the commit's labels to the pushed image, under the same tag."""
    args = [crane, "mutate"]
    if insecure:
        args.append("--insecure")
    for key, value in sorted(labels.items()):
        args += ["--label", f"{key}={value}"]
    return [*args, image]


def push_args(nerdctl: str, req: PushRequest) -> list[str]:
    args = [nerdctl, "--namespace", CRI_NAMESPACE]
    if req.insecure:
        args.append("--insecure-registry")
    return [*args, "push", req.image]


def docker_config(req: PushRequest) -> dict[str, object]:
    if req.username is None or req.password is None:
        return {"auths": {}}
    registry = req.image.split("/", 1)[0]
    auth = base64.b64encode(f"{req.username}:{req.password}".encode()).decode()
    return {"auths": {registry: {"auth": auth}}}


def cri_labels(inspected: Any) -> dict[str, str]:
    """The labels of a container from `nerdctl inspect --mode=native`."""
    entry = inspected[0] if isinstance(inspected, list) and inspected else inspected
    if not isinstance(entry, dict):
        return {}
    labels = entry.get("Labels") or (entry.get("Spec") or {}).get("Labels") or {}
    return {str(k): str(v) for k, v in labels.items()} if isinstance(labels, dict) else {}


def check_kernel_pod(pod: Mapping[str, Any], container_id: str, node_name: str | None) -> None:
    """Refuse a container that is not the kernel container of a session Pod on this node."""
    meta, spec, status = pod["metadata"], pod.get("spec") or {}, pod.get("status") or {}
    if (meta.get("labels") or {}).get(LABEL_MANAGED_BY) != MANAGED_BY:
        raise NodeHelperCommandError("the container does not belong to a Backend.AI session")
    if node_name is not None and spec.get("nodeName") != node_name:
        raise NodeHelperCommandError("the container runs on another node")
    kernel = next(
        (c for c in status.get("containerStatuses") or [] if c.get("name") == KERNEL_CONTAINER),
        None,
    )
    if kernel is None or str(kernel.get("containerID", "")).split("://", 1)[-1] != container_id:
        raise NodeHelperCommandError("the container is not the kernel container of its Pod")


def _write_config(config_dir: Path, config: Mapping[str, object]) -> None:
    """The registry credentials, readable only by the helper."""
    path = config_dir / "config.json"
    path.touch(mode=0o600)
    path.write_text(json.dumps(config))


async def _run(args: Sequence[str], env: dict[str, str] | None = None) -> str:
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        env=env,
    )
    out, _ = await proc.communicate()
    text = out.decode(errors="replace")
    if proc.returncode != 0:
        raise NodeHelperCommandError(
            f"{args[3] if len(args) > 3 else args[0]} failed: {text[-2000:]}"
        )
    return text


def kube_verifier(nerdctl: str, api: client.ApiClient, node_name: str | None) -> ContainerVerifier:
    """Verify a container through its CRI labels and its Pod in the Kubernetes API."""
    core = client.CoreV1Api(api)

    async def verify(container_id: str) -> None:
        try:
            inspected = json.loads(await _run(inspect_args(nerdctl, container_id)))
        except ValueError as e:
            raise NodeHelperCommandError("the container is not inspectable") from e
        labels = cri_labels(inspected)
        namespace, name = labels.get(CRI_POD_NAMESPACE), labels.get(CRI_POD_NAME)
        if not namespace or not name or labels.get(CRI_CONTAINER_NAME) != KERNEL_CONTAINER:
            raise NodeHelperCommandError("the container is not a kernel container")
        try:
            pod = await core.read_namespaced_pod(name, namespace)
        except ApiException as e:
            raise NodeHelperCommandError("the Pod of the container is not found") from e
        check_kernel_pod(api.sanitize_for_serialization(pod), container_id, node_name)

    return verify


def build_app(
    nerdctl: str,
    token: str,
    verify: ContainerVerifier,
    crane: str = "/usr/local/bin/crane",
) -> web.Application:
    # Commands are heavy (a commit copies the container's layer): run a few at a time.
    slots = asyncio.Semaphore(MAX_CONCURRENT_COMMANDS)

    @web.middleware
    async def authenticate(request: web.Request, handler: Handler) -> web.StreamResponse:
        given = request.headers.get(TOKEN_HEADER, "")
        if not token or not hmac.compare_digest(given.encode(), token.encode()):
            return web.json_response({"error": "unauthorized"}, status=401)
        return await handler(request)

    async def commit(request: web.Request) -> web.Response:
        try:
            req = CommitRequest.model_validate(await request.json())
        except (ValidationError, ValueError) as e:
            return web.json_response({"error": str(e)}, status=400)
        try:
            await verify(req.container_id)
        except NodeHelperCommandError as e:
            log.trace("session commit refused", image=req.image, reason=str(e.extra_msg))
            return web.json_response({"error": str(e.extra_msg)}, status=403)
        async with slots:
            try:
                await _run(commit_args(nerdctl, req))
            except NodeHelperCommandError as e:
                log.warning("session commit failed", image=req.image, exc_info=e)
                return web.json_response({"error": str(e.extra_msg)}, status=500)
        log.trace("session committed", image=req.image)
        return web.json_response({"image": req.image})

    async def push(request: web.Request) -> web.Response:
        try:
            req = PushRequest.model_validate(await request.json())
        except (ValidationError, ValueError) as e:
            return web.json_response({"error": str(e)}, status=400)
        async with slots:
            with tempfile.TemporaryDirectory() as config_dir:
                await asyncio.to_thread(_write_config, Path(config_dir), docker_config(req))
                env = {"DOCKER_CONFIG": config_dir, "HOME": config_dir}
                try:
                    await _run(push_args(nerdctl, req), env=env)
                    if req.labels:
                        await _run(label_args(crane, req.image, req.labels, req.insecure), env=env)
                except NodeHelperCommandError as e:
                    log.warning("image push failed", image=req.image, exc_info=e)
                    return web.json_response({"error": str(e.extra_msg)}, status=500)
        log.trace("image pushed", image=req.image)
        return web.json_response({"image": req.image})

    app = web.Application(middlewares=[authenticate])
    app.router.add_post("/v1/commit", commit)
    app.router.add_post("/v1/push", push)
    return app
