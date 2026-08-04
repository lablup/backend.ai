from __future__ import annotations

import base64
import json
import os
import secrets
import time
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Final

from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

from ai.backend.common.cc_storage import FORMAT_ID
from ai.backend.common.types import VFolderConfidential, VFolderID, VFolderMount

from ..errors.confidential import FolderEscrowUnreachable, FolderEncryptionMissing
from ..models.scaling_group.types import ConfidentialScalingGroupOpts
from .broker import BrokerClient, BrokerTarget

FOLDER_KEY_BYTES: Final = 32
DEFAULT_TIER: Final = "file"
DEFAULT_FORMAT: Final = FORMAT_ID
MOUNT_PLAN_VERSION: Final = 1
SCRATCH_DEVICE: Final = "/dev/bai_scratch"


def folder_key_path(domain_name: str, folder_id: uuid.UUID) -> str:
    return f"{domain_name}/vfolder/{folder_id.hex}"


def folder_key_tag(vfid: VFolderID) -> str:
    return f"folder-key-{vfid.folder_id.hex}"


class FolderKeyEscrow:
    def __init__(self, path: Path, key: bytes) -> None:
        self._path = path
        self._aead = ChaCha20Poly1305(key)

    def append(self, resource_path: str, payload: bytes) -> None:
        nonce = secrets.token_bytes(12)
        record = {
            "at": int(time.time()),
            "path": resource_path,
            "nonce": base64.b64encode(nonce).decode(),
            "sealed": base64.b64encode(
                self._aead.encrypt(nonce, payload, resource_path.encode())
            ).decode(),
        }
        try:
            self._path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with open(self._path, "a") as backup:
                backup.write(json.dumps(record, sort_keys=True) + "\n")
                backup.flush()
                os.fsync(backup.fileno())
        except OSError as error:
            raise FolderEscrowUnreachable(extra_msg=f"{self._path}: {error}") from error

    def entries(self) -> dict[str, bytes]:
        held: dict[str, bytes] = {}
        try:
            lines = self._path.read_text().splitlines()
        except FileNotFoundError:
            return held
        except OSError as error:
            raise FolderEscrowUnreachable(extra_msg=f"{self._path}: {error}") from error
        for line in lines:
            record = json.loads(line)
            resource_path = record["path"]
            payload = self._aead.decrypt(
                base64.b64decode(record["nonce"]),
                base64.b64decode(record["sealed"]),
                resource_path.encode(),
            )
            if payload:
                held[resource_path] = payload
            else:
                held.pop(resource_path, None)
        return held

    def held(self, resource_path: str) -> bytes | None:
        return self.entries().get(resource_path)


class FolderKeyCustodian:
    def __init__(self, broker: BrokerClient) -> None:
        self._broker = broker

    def escrow(self, opts: ConfidentialScalingGroupOpts) -> FolderKeyEscrow:
        if not opts.folder_key_escrow_path or not opts.folder_key_escrow_key:
            raise FolderEscrowUnreachable(
                extra_msg="the scaling group names no folder-key escrow, so no key may be minted"
            )
        return FolderKeyEscrow(
            Path(opts.folder_key_escrow_path),
            base64.b64decode(opts.folder_key_escrow_key),
        )

    async def mint(
        self, opts: ConfidentialScalingGroupOpts, domain_name: str, folder_id: uuid.UUID
    ) -> str:
        resource_path = folder_key_path(domain_name, folder_id)
        escrow = self.escrow(opts)
        key = secrets.token_bytes(FOLDER_KEY_BYTES)
        escrow.append(resource_path, key)
        await self._broker.put_resource(BrokerTarget.of(opts), resource_path, key)
        return resource_path

    async def revoke(
        self, opts: ConfidentialScalingGroupOpts, domain_name: str, folder_id: uuid.UUID
    ) -> None:
        resource_path = folder_key_path(domain_name, folder_id)
        self.escrow(opts).append(resource_path, b"")
        await self._broker.destroy_resource(BrokerTarget.of(opts), resource_path)

    def release(
        self, opts: ConfidentialScalingGroupOpts, domain_name: str, folder_id: uuid.UUID
    ) -> bytes:
        key = self.escrow(opts).held(folder_key_path(domain_name, folder_id))
        if key is None:
            raise FolderEncryptionMissing(
                extra_msg=f"no folder key is held for {folder_id}; the folder predates encryption"
            )
        return key

    async def restore(self, opts: ConfidentialScalingGroupOpts) -> int:
        target = BrokerTarget.of(opts)
        held = self.escrow(opts).entries()
        for resource_path, payload in held.items():
            await self._broker.put_resource(target, resource_path, payload)
        return len(held)


def describe(
    export: Mapping[str, str] | None, domain_name: str, vfid: VFolderID
) -> VFolderConfidential | None:
    if not export:
        return None
    return VFolderConfidential(
        transport=export["transport"],
        source=export["source"],
        options=export.get("options", ""),
        tier=DEFAULT_TIER,
        format=DEFAULT_FORMAT,
        key_path=folder_key_path(domain_name, vfid.folder_id),
    )


def mount_plan(mounts: list[VFolderMount], scratch_tag: str | None) -> bytes:
    entries = []
    for mount in mounts:
        descriptor = mount.confidential
        if descriptor is None:
            raise FolderEncryptionMissing(extra_msg=f"folder {mount.name} carries no descriptor")
        entries.append({
            "name": mount.name,
            "kind": descriptor.transport,
            "source": descriptor.source,
            "options": descriptor.options,
            "target": str(mount.kernel_path),
            "read_only": mount.mount_perm.value == "ro",
            "encryption": {
                "tier": descriptor.tier,
                "format": descriptor.format,
                "key_tag": folder_key_tag(mount.vfid),
            },
        })
    plan: dict[str, object] = {"version": MOUNT_PLAN_VERSION, "mounts": entries}
    if scratch_tag is not None:
        plan["scratch"] = {
            "device": SCRATCH_DEVICE,
            "target": "/home/work",
            "key_tag": scratch_tag,
        }
    return json.dumps(plan, sort_keys=True).encode()
