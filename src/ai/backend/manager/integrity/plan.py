from __future__ import annotations

import uuid
from typing import Any, Final

from ai.backend.manager.integrity.lease import MountLease

TIER_DISCLOSURE: Final = (
    "encrypted and tamper-evident per sector — the storage operator cannot read this folder, and"
    " cannot modify or selectively roll back anything inside it without the guest detecting it on"
    " read. A wholesale restore of the entire image to an earlier consistent state remains"
    " undetectable, and the folder carries one active mount at a time."
)

CONSTRUCTION: Final[dict[str, Any]] = {
    "sector_size": 4096,
    "tag_size": 32,
    "integrity_algorithm": "hmac-sha256",
    "journal": True,
    "cipher": "aes-xts-plain64",
    "key_bits": 512,
    "direct_io": True,
}


def mount_plan_entry(
    folder_id: uuid.UUID,
    image: str,
    target: str,
    key_resource: str,
    lease_resource: str,
    lease: MountLease,
    lease_poll: float = 60.0,
) -> dict[str, Any]:
    return {
        **CONSTRUCTION,
        "tier": "integrity",
        "folder": str(folder_id),
        "name": f"bai-{folder_id.hex[:16]}",
        "image": image,
        "target": target,
        "key_resource": key_resource,
        "lease_resource": lease_resource,
        "holder": str(lease.holder),
        "epoch": lease.epoch,
        "lease_poll": lease_poll,
        "disclosure": TIER_DISCLOSURE,
    }
