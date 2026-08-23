"""Minimal OCI/Docker registry client for the enroot backend.

enroot's ``.sqsh`` files carry no queryable OCI config, so the sidecar metadata
(:mod:`ai.backend.agent.enroot.runtime`) — the config-blob digest + kernel-spec/base-distro
labels + architecture + entrypoint — is fetched straight from the registry at import time. Just
enough of the registry v2 API to read a manifest and its config blob; auth reuses the shared
``ai.backend.common.docker.login`` (bearer-token or basic).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import aiohttp
import yarl

from ai.backend.common.docker import login
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__name__))

_DOCKER_HUB_REGISTRY = "registry-1.docker.io"
_MANIFEST_ACCEPT = ", ".join([
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.oci.image.manifest.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
    "application/vnd.docker.distribution.manifest.v2+json",
])
_INDEX_MEDIA_TYPES = frozenset({
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
})
# Push in Docker schema2 rather than OCI: it is what every registry and every runtime in this
# stack (docker, containerd, enroot's own `import docker://`) accepts without configuration.
_MANIFEST_MEDIA_TYPE = "application/vnd.docker.distribution.manifest.v2+json"
_CONFIG_MEDIA_TYPE = "application/vnd.docker.container.image.v1+json"
_LAYER_MEDIA_TYPE = "application/vnd.docker.image.rootfs.diff.tar.gzip"
_BLOB_UPLOAD_CHUNK = 4 * 1024 * 1024


@dataclass(frozen=True)
class ImageMetadata:
    config_digest: str
    architecture: str
    labels: Mapping[str, str]
    # Entrypoint and Cmd are kept APART. Collapsing them loses the difference between "always
    # runs this" and "runs this unless told otherwise", and republishing a Cmd as an Entrypoint
    # silently changes what `docker run <image> <cmd>` means.
    entrypoint: list[str] | None
    cmd: list[str] | None
    env: list[str] | None
    working_dir: str | None


@dataclass(frozen=True)
class _Ref:
    registry: str
    repo: str
    reference: str  # tag or digest
    insecure: bool


def _parse_ref(canonical: str) -> _Ref:
    # [registry[:port]/]repo[/sub...][:tag|@digest]. A first path component with '.'/':' or
    # 'localhost' is the registry host; otherwise it is Docker Hub (single names get 'library/').
    if "@" in canonical:
        name, _, reference = canonical.partition("@")
    else:
        colon = canonical.rfind(":")
        if colon > canonical.rfind("/"):  # a ':' after the last '/' is a tag, not a registry port
            name, reference = canonical[:colon], canonical[colon + 1 :]
        else:
            name, reference = canonical, "latest"
    head, slash, rest = name.partition("/")
    if slash and ("." in head or ":" in head or head == "localhost"):
        registry, repo = head, rest
    else:
        registry, repo = _DOCKER_HUB_REGISTRY, name if slash else f"library/{name}"
    insecure = registry != _DOCKER_HUB_REGISTRY and (":" in registry or registry == "localhost")
    return _Ref(registry=registry, repo=repo, reference=reference, insecure=insecure)


def _registry_url(ref: _Ref, scheme: str) -> yarl.URL:
    return yarl.URL(f"{scheme}://{ref.registry}")


async def _get_json(
    sess: aiohttp.ClientSession, url: yarl.URL, req_kwargs: Mapping[str, Any], accept: str
) -> dict[str, Any]:
    headers = {**dict(req_kwargs.get("headers", {})), "Accept": accept}
    kwargs = {k: v for k, v in req_kwargs.items() if k != "headers"}
    async with sess.get(url, headers=headers, **kwargs) as resp:
        resp.raise_for_status()
        data = json.loads(await resp.read())
    return data if isinstance(data, dict) else {}


async def fetch_image_metadata(
    canonical: str, auth: Mapping[str, str] | None, *, architecture: str = "amd64"
) -> ImageMetadata | None:
    """Fetch the config-blob digest + labels + architecture + entrypoint for ``canonical``.

    Returns ``None`` (and logs) rather than raising, so a metadata probe never breaks a pull.
    """
    ref = _parse_ref(canonical)
    credentials = dict(auth or {})
    schemes = ("http",) if ref.insecure else ("https", "http")
    last_err: Exception | None = None
    for scheme in schemes:
        try:
            return await _fetch_one(ref, scheme, credentials, architecture)
        except Exception as e:
            # A metadata probe must never break the pull; try the next scheme, else warn + null.
            last_err = e
    log.warning("[enroot] image metadata probe failed for {}: {}", canonical, last_err)
    return None


async def _fetch_one(
    ref: _Ref, scheme: str, credentials: Mapping[str, Any], architecture: str
) -> ImageMetadata:
    registry_url = _registry_url(ref, scheme)
    async with aiohttp.ClientSession() as sess:
        req_kwargs = await login(
            sess, registry_url, dict(credentials), scope=f"repository:{ref.repo}:pull"
        )
        manifest = await _get_json(
            sess,
            registry_url / "v2" / ref.repo / "manifests" / ref.reference,
            req_kwargs,
            _MANIFEST_ACCEPT,
        )
        if manifest.get("mediaType") in _INDEX_MEDIA_TYPES:
            manifest = await _resolve_index(
                sess, registry_url, ref, req_kwargs, manifest, architecture
            )
        config_digest = manifest["config"]["digest"]
        config = await _get_json(
            sess,
            registry_url / "v2" / ref.repo / "blobs" / config_digest,
            req_kwargs,
            "application/vnd.oci.image.config.v1+json",
        )
    cfg = config.get("config") or {}
    return ImageMetadata(
        config_digest=config_digest,
        architecture=str(config.get("architecture") or architecture),
        labels=dict(cfg.get("Labels") or {}),
        entrypoint=list(cfg["Entrypoint"]) if cfg.get("Entrypoint") else None,
        cmd=list(cfg["Cmd"]) if cfg.get("Cmd") else None,
        env=list(cfg["Env"]) if cfg.get("Env") else None,
        working_dir=str(cfg["WorkingDir"]) if cfg.get("WorkingDir") else None,
    )


async def _resolve_index(
    sess: aiohttp.ClientSession,
    registry_url: yarl.URL,
    ref: _Ref,
    req_kwargs: Mapping[str, Any],
    index: Mapping[str, Any],
    architecture: str,
) -> dict[str, Any]:
    for entry in index.get("manifests", []):
        platform = entry.get("platform") or {}
        if platform.get("architecture") == architecture and platform.get("os") == "linux":
            return await _get_json(
                sess,
                registry_url / "v2" / ref.repo / "manifests" / entry["digest"],
                req_kwargs,
                _MANIFEST_ACCEPT,
            )
    raise RuntimeError(f"no {architecture}/linux manifest in index for {ref.repo}:{ref.reference}")


async def push_image(
    canonical: str,
    *,
    layer_path: Path,
    layer_diff_id: str,
    config: Mapping[str, Any],
    auth: Mapping[str, str] | None,
) -> str:
    """Publish a single-layer image and return its manifest digest.

    ``layer_path`` is a gzipped tar of the whole rootfs and ``layer_diff_id`` its *uncompressed*
    digest, which is what the config's ``rootfs.diff_ids`` records — the manifest references the
    compressed blob, the config the uncompressed one, and a registry will reject a mismatch.

    A committed enroot image is one squashed layer by nature: `enroot export` produces a full
    rootfs snapshot, not a stack of diffs, so there is nothing to preserve layering from.
    """
    ref = _parse_ref(canonical)
    # Own the rootfs stanza rather than trusting the caller to pair it correctly: the manifest
    # references the COMPRESSED layer digest and the config the UNCOMPRESSED one, and a registry
    # rejects the image if they are crossed. Keeping both in one place makes that unmixable.
    full_config = {**config, "rootfs": {"type": "layers", "diff_ids": [layer_diff_id]}}
    config_bytes = json.dumps(full_config, separators=(",", ":"), sort_keys=True).encode()
    config_digest = f"sha256:{hashlib.sha256(config_bytes).hexdigest()}"
    layer_size = layer_path.stat().st_size
    layer_digest = await asyncio.to_thread(_file_digest, layer_path)
    manifest = {
        "schemaVersion": 2,
        "mediaType": _MANIFEST_MEDIA_TYPE,
        "config": {
            "mediaType": _CONFIG_MEDIA_TYPE,
            "digest": config_digest,
            "size": len(config_bytes),
        },
        "layers": [
            {"mediaType": _LAYER_MEDIA_TYPE, "digest": layer_digest, "size": layer_size},
        ],
    }
    manifest_bytes = json.dumps(manifest, separators=(",", ":")).encode()

    schemes = ("http",) if ref.insecure else ("https", "http")
    last_err: Exception | None = None
    for scheme in schemes:
        try:
            await _push_one(
                ref,
                scheme,
                dict(auth or {}),
                config_bytes,
                config_digest,
                layer_path,
                layer_digest,
                manifest_bytes,
            )
            return f"sha256:{hashlib.sha256(manifest_bytes).hexdigest()}"
        except Exception as e:
            last_err = e
    raise RuntimeError(f"pushing {canonical} failed: {last_err}") from last_err


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(_BLOB_UPLOAD_CHUNK):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


async def _push_one(
    ref: _Ref,
    scheme: str,
    credentials: Mapping[str, Any],
    config_bytes: bytes,
    config_digest: str,
    layer_path: Path,
    layer_digest: str,
    manifest_bytes: bytes,
) -> None:
    registry_url = _registry_url(ref, scheme)
    # A push token is a different scope from a pull one; asking for pull as well keeps the HEAD
    # blob checks below on the same token.
    async with aiohttp.ClientSession() as sess:
        req_kwargs = await login(
            sess, registry_url, dict(credentials), scope=f"repository:{ref.repo}:push,pull"
        )
        base = registry_url / "v2" / ref.repo
        await _upload_blob(sess, base, req_kwargs, layer_digest, body=layer_path)
        await _upload_blob(sess, base, req_kwargs, config_digest, body=config_bytes)
        headers = {**dict(req_kwargs.get("headers", {})), "Content-Type": _MANIFEST_MEDIA_TYPE}
        kwargs = {k: v for k, v in req_kwargs.items() if k != "headers"}
        async with sess.put(
            base / "manifests" / ref.reference, data=manifest_bytes, headers=headers, **kwargs
        ) as resp:
            if resp.status >= 400:
                raise RuntimeError(
                    f"manifest PUT failed ({resp.status}): {(await resp.text())[:400]}"
                )


async def _upload_blob(
    sess: aiohttp.ClientSession,
    base: yarl.URL,
    req_kwargs: Mapping[str, Any],
    digest: str,
    *,
    body: Path | bytes,
) -> None:
    """Upload one blob, skipping it when the registry already has it.

    Monolithic: open a session, then PUT the whole body with `?digest=`. The chunked flow exists
    for resumability, which a commit does not need — and every registry accepts this form.
    """
    headers = dict(req_kwargs.get("headers", {}))
    kwargs = {k: v for k, v in req_kwargs.items() if k != "headers"}
    async with sess.head(base / "blobs" / digest, headers=headers, **kwargs) as resp:
        if resp.status == 200:
            log.debug("[enroot] registry already has {}", digest)
            return
    async with sess.post(base / "blobs" / "uploads" / "", headers=headers, **kwargs) as resp:
        if resp.status not in (200, 202):
            raise RuntimeError(f"blob upload POST failed ({resp.status}): {await resp.text()}")
        location = resp.headers.get("Location")
    if not location:
        raise RuntimeError("blob upload POST returned no Location")
    # The Location may be absolute or registry-relative; join handles both.
    upload_url = base.join(yarl.URL(location)).update_query({"digest": digest})
    if isinstance(body, Path):
        size = body.stat().st_size
        with body.open("rb") as f:
            await _put_blob(sess, upload_url, f, size, headers, kwargs, digest)
    else:
        await _put_blob(sess, upload_url, body, len(body), headers, kwargs, digest)


async def _put_blob(
    sess: aiohttp.ClientSession,
    url: yarl.URL,
    body: Any,
    size: int,
    headers: Mapping[str, str],
    kwargs: Mapping[str, Any],
    digest: str,
) -> None:
    put_headers = {
        **headers,
        "Content-Type": "application/octet-stream",
        "Content-Length": str(size),
    }
    async with sess.put(url, data=body, headers=put_headers, **kwargs) as resp:
        if resp.status not in (200, 201, 202):
            raise RuntimeError(
                f"blob PUT failed for {digest} ({resp.status}): {(await resp.text())[:400]}"
            )
