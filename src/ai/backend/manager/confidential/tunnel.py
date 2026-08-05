from __future__ import annotations

import base64
import ipaddress
import json
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Final

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)

from ai.backend.manager.models.confidential.types import SessionResourceKind
from ai.backend.manager.models.scaling_group.types import NONCE_RESIDUAL_DISCLOSURE

TUNNEL_SUBNET: Final = ipaddress.IPv4Network("10.252.0.0/16")
TUNNEL_PORT: Final = 51820
PEER_DIRECTORY_TAG: Final = "tunnel-peers"
CONFIDENTIAL_NETWORK_PREFIX: Final = "bai-confidential-"


@dataclass(frozen=True)
class TunnelMember:
    kernel_id: uuid.UUID
    cluster_idx: int
    hostname: str
    endpoint: str

    @property
    def tag(self) -> str:
        return f"tunnel-{self.kernel_id}"

    @property
    def tunnel_addr(self) -> str:
        return str(TUNNEL_SUBNET[1 + self.cluster_idx])


def _encode(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def _document(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True).encode("utf-8")


def tunnel_resources(
    members: Sequence[TunnelMember],
) -> dict[str, tuple[SessionResourceKind, bytes]]:
    keys = {member.kernel_id: X25519PrivateKey.generate() for member in members}
    directory = _document({
        "port": TUNNEL_PORT,
        "subnet": str(TUNNEL_SUBNET),
        "residual": NONCE_RESIDUAL_DISCLOSURE,
        "peers": [
            {
                "cluster_idx": member.cluster_idx,
                "hostname": member.hostname,
                "tunnel_addr": member.tunnel_addr,
                "endpoint": member.endpoint,
                "public_key": _encode(
                    keys[member.kernel_id].public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
                ),
            }
            for member in sorted(members, key=lambda m: m.cluster_idx)
        ],
    })
    resources: dict[str, tuple[SessionResourceKind, bytes]] = {
        PEER_DIRECTORY_TAG: (SessionResourceKind.PEER_DIRECTORY, directory)
    }
    for member in members:
        resources[member.tag] = (
            SessionResourceKind.TUNNEL_KEY,
            _document({
                "cluster_idx": member.cluster_idx,
                "private_key": _encode(
                    keys[member.kernel_id].private_bytes(
                        Encoding.Raw, PrivateFormat.Raw, NoEncryption()
                    )
                ),
            }),
        )
    return resources
