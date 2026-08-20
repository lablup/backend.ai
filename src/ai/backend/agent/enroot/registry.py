"""Minimal OCI/Docker registry client for the enroot backend.

enroot's ``.sqsh`` files carry no queryable OCI config, so the sidecar metadata
(:mod:`ai.backend.agent.enroot.runtime`) — the config-blob digest + kernel-spec/base-distro
labels + architecture + entrypoint — is fetched straight from the registry at import time. Just
enough of the registry v2 API to read a manifest and its config blob; auth reuses the shared
``ai.backend.common.docker.login`` (bearer-token or basic).
"""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from dataclasses import dataclass
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


@dataclass(frozen=True)
class ImageMetadata:
    config_digest: str
    architecture: str
    labels: Mapping[str, str]
    entrypoint: list[str] | None


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
    entrypoint = cfg.get("Entrypoint") or cfg.get("Cmd")
    return ImageMetadata(
        config_digest=config_digest,
        architecture=str(config.get("architecture") or architecture),
        labels=dict(cfg.get("Labels") or {}),
        entrypoint=list(entrypoint) if entrypoint else None,
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
