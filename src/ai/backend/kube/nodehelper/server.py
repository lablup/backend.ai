"""node helper: what the Agent did with the container engine of its node and a Pod cannot,
here a session commit and its push (suggestion-1122 9.2). One per node, beside containerd.

`nerdctl` works on the CRI namespace (`k8s.io`), where the kubelet's containers live. It has no
LABEL change for a commit, so the labels go onto the pushed image in the registry (`crane`).
"""

from __future__ import annotations

import asyncio
import base64
import hmac
import json
import logging
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Final

from aiohttp import web
from aiohttp.typedefs import Handler
from pydantic import BaseModel, Field

from ai.backend.kube.errors import NodeHelperCommandError
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

CRI_NAMESPACE: Final = "k8s.io"
TOKEN_HEADER: Final = "X-BackendAI-Node-Helper-Token"


class CommitRequest(BaseModel):
    container_id: str
    image: str = Field(description="Canonical name the commit is tagged with")
    labels: dict[str, str] = Field(default_factory=dict)


class PushRequest(BaseModel):
    image: str
    username: str | None = None
    password: str | None = None
    insecure: bool = False


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


def label_args(crane: str, image: str, labels: dict[str, str], insecure: bool) -> list[str]:
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


def build_app(nerdctl: str, token: str, crane: str = "/usr/local/bin/crane") -> web.Application:
    pending_labels: dict[str, dict[str, str]] = {}  # committed image → labels for its push

    @web.middleware
    async def authenticate(request: web.Request, handler: Handler) -> web.StreamResponse:
        given = request.headers.get(TOKEN_HEADER, "")
        if not hmac.compare_digest(given, token):
            return web.json_response({"error": "unauthorized"}, status=401)
        return await handler(request)

    async def commit(request: web.Request) -> web.Response:
        req = CommitRequest.model_validate(await request.json())
        try:
            await _run(commit_args(nerdctl, req))
        except NodeHelperCommandError as e:
            log.warning("session commit failed", image=req.image, exc_info=e)
            return web.json_response({"error": str(e)}, status=500)
        pending_labels[req.image] = dict(req.labels)
        log.trace("session committed", image=req.image)
        return web.json_response({"image": req.image})

    async def push(request: web.Request) -> web.Response:
        req = PushRequest.model_validate(await request.json())
        with tempfile.TemporaryDirectory() as config_dir:
            Path(config_dir, "config.json").write_text(json.dumps(docker_config(req)))
            env = {"DOCKER_CONFIG": config_dir, "HOME": config_dir}
            try:
                await _run(push_args(nerdctl, req), env=env)
                if labels := pending_labels.pop(req.image, None):
                    await _run(label_args(crane, req.image, labels, req.insecure), env=env)
            except NodeHelperCommandError as e:
                log.warning("image push failed", image=req.image, exc_info=e)
                return web.json_response({"error": str(e)}, status=500)
        log.trace("image pushed", image=req.image)
        return web.json_response({"image": req.image})

    app = web.Application(middlewares=[authenticate])
    app.router.add_post("/v1/commit", commit)
    app.router.add_post("/v1/push", push)
    return app
