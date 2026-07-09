"""Wire protocol for the privileged network helper (BEP-1058).

The unprivileged agent and the privileged (CAP_NET_ADMIN) helper speak a small,
**semantic** RPC over a unix socket: newline-delimited JSON, one request and one
response per line. The vocabulary is deliberately tiny and carries only opaque
identifiers (``session_id`` / ``container_id``) plus the manager-provided network
parameters — never argv, device names, netns paths, or CNI config. The helper
derives every side-effecting value itself (see ``server.py``), so a compromised
agent cannot inject commands, target an arbitrary namespace, or name an arbitrary
device: the attack surface is the enum of verbs below, nothing more.

Keeping this module pure (dataclasses + encode/decode, no I/O) makes the protocol
unit-testable on both ends.
"""

from __future__ import annotations

import enum
import json
from dataclasses import dataclass
from typing import Any


class HelperOp(enum.StrEnum):
    SETUP_SESSION = "setup_session"
    TEARDOWN_SESSION = "teardown_session"
    ATTACH_CONTAINER = "attach_container"
    DETACH_CONTAINER = "detach_container"


class ProtocolError(RuntimeError):
    """Malformed frame or unknown/typed field — a client that violates the wire
    contract. Never carries privileged detail back to the caller."""


@dataclass(frozen=True)
class HelperRequest:
    """A single semantic request. ``network_config`` is only present for
    SETUP_SESSION and is the manager's ``{backend, subnet, vni, mtu}`` — the helper
    still validates it (untrusted: it arrives via the agent)."""

    op: HelperOp
    session_id: str
    container_id: str | None = None
    network_config: dict[str, Any] | None = None

    def encode(self) -> bytes:
        payload: dict[str, Any] = {"op": str(self.op), "session_id": self.session_id}
        if self.container_id is not None:
            payload["container_id"] = self.container_id
        if self.network_config is not None:
            payload["network_config"] = self.network_config
        return json.dumps(payload, separators=(",", ":")).encode() + b"\n"

    @classmethod
    def decode(cls, line: bytes) -> HelperRequest:
        try:
            data = json.loads(line)
        except (ValueError, TypeError) as e:
            raise ProtocolError("invalid JSON frame") from e
        if not isinstance(data, dict):
            raise ProtocolError("frame is not an object")
        try:
            op = HelperOp(data["op"])
        except (KeyError, ValueError) as e:
            raise ProtocolError("missing or unknown op") from e
        session_id = data.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise ProtocolError("missing session_id")
        container_id = data.get("container_id")
        if container_id is not None and not isinstance(container_id, str):
            raise ProtocolError("container_id must be a string")
        network_config = data.get("network_config")
        if network_config is not None and not isinstance(network_config, dict):
            raise ProtocolError("network_config must be an object")
        return cls(
            op=op,
            session_id=session_id,
            container_id=container_id,
            network_config=network_config,
        )


@dataclass(frozen=True)
class HelperResponse:
    """Result of one request. ``assigned`` maps a NetworkRole name to the assigned
    IP (only for ATTACH). ``error`` is a short, non-privileged reason string."""

    ok: bool
    assigned: dict[str, str] | None = None
    error: str | None = None

    def encode(self) -> bytes:
        payload: dict[str, Any] = {"ok": self.ok}
        if self.assigned is not None:
            payload["assigned"] = self.assigned
        if self.error is not None:
            payload["error"] = self.error
        return json.dumps(payload, separators=(",", ":")).encode() + b"\n"

    @classmethod
    def decode(cls, line: bytes) -> HelperResponse:
        try:
            data = json.loads(line)
        except (ValueError, TypeError) as e:
            raise ProtocolError("invalid JSON frame") from e
        if not isinstance(data, dict) or "ok" not in data:
            raise ProtocolError("malformed response")
        assigned = data.get("assigned")
        if assigned is not None and not isinstance(assigned, dict):
            raise ProtocolError("assigned must be an object")
        error = data.get("error")
        return cls(ok=bool(data["ok"]), assigned=assigned, error=error)
