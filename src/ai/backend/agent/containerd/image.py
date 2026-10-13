"""Resolve an imported image to its rootfs chain ID and runtime config."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Final

from ai.backend.agent.containerd.client import ContainerdAPI
from ai.backend.agent.errors.containerd import ContainerdImageInvalid

_INDEX_MEDIA_TYPES: Final = frozenset({
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
})
_GOARCH: Final[Mapping[str, str]] = {"x86_64": "amd64", "aarch64": "arm64"}


@dataclass(frozen=True)
class ResolvedImage:
    chain_id: str
    env: Sequence[str] = ()
    working_dir: str = ""
    entrypoint: Sequence[str] = ()
    cmd: Sequence[str] = ()
    user: str = ""
    labels: Mapping[str, str] = field(default_factory=dict)


def chain_id(diff_ids: Sequence[str]) -> str:
    """The OCI chain ID of the layers, which names the snapshot of the unpacked image."""
    if not diff_ids:
        raise ContainerdImageInvalid("the image config has no rootfs layers")
    chain = diff_ids[0]
    for diff_id in diff_ids[1:]:
        chain = "sha256:" + hashlib.sha256(f"{chain} {diff_id}".encode()).hexdigest()
    return chain


def select_manifest_digest(index: Mapping[str, Any], arch: str) -> str:
    """The digest of the linux manifest for `arch` (a machine name such as `x86_64`) in an index."""
    goarch = _GOARCH.get(arch, arch)
    for entry in index.get("manifests", []):
        platform = entry.get("platform") or {}
        if platform.get("os") == "linux" and platform.get("architecture") == goarch:
            return str(entry["digest"])
    raise ContainerdImageInvalid(f"the image index has no linux/{goarch} manifest")


def parse_image_config(config: Mapping[str, Any]) -> ResolvedImage:
    runtime = config.get("config") or {}
    return ResolvedImage(
        chain_id=chain_id((config.get("rootfs") or {}).get("diff_ids") or []),
        env=tuple(runtime.get("Env") or ()),
        working_dir=runtime.get("WorkingDir") or "",
        entrypoint=tuple(runtime.get("Entrypoint") or ()),
        cmd=tuple(runtime.get("Cmd") or ()),
        user=runtime.get("User") or "",
        labels=dict(runtime.get("Labels") or {}),
    )


async def _read_json(client: ContainerdAPI, digest: str) -> Mapping[str, Any]:
    try:
        data = json.loads(await client.read_blob(digest))
    except ValueError as e:
        raise ContainerdImageInvalid(f"the blob {digest} is not valid JSON") from e
    if not isinstance(data, dict):
        raise ContainerdImageInvalid(f"the blob {digest} is not a JSON object")
    return data


async def resolve_image(client: ContainerdAPI, image_ref: str, arch: str) -> ResolvedImage:
    """Follow image, then index (if any), manifest and config blobs of the pre-imported image."""
    target = await client.get_image_target(image_ref)
    manifest_digest = target.digest
    if target.media_type in _INDEX_MEDIA_TYPES:
        index = await _read_json(client, target.digest)
        manifest_digest = select_manifest_digest(index, arch)
    manifest = await _read_json(client, manifest_digest)
    config_digest = (manifest.get("config") or {}).get("digest")
    if not config_digest:
        raise ContainerdImageInvalid(f"the manifest of {image_ref} names no config blob")
    return parse_image_config(await _read_json(client, config_digest))
