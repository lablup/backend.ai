"""Which SESSION owns a VNI on this node, and under what configuration.

The privnet exists because the agent is not trusted with privileged host networking, but the
network configuration it submits was taken at face value: any VNI, port, MTU, subnet and key the
agent asked for. A compromised or confused agent could therefore name a VNI another session --
possibly another agent's -- is already running on, and setup would delete `baivx<vni>`,
`baibr<vni>` and the LOCAL bridge before rebuilding them, cutting that session's containers off
the network. The conflict check could not catch it either: it treats every `baivx*` device as
"ours", which is exactly what the attacker's declaration claims to be.

So the binding is recorded where every agent on the host can see it, and it is immutable while it
lasts: a VNI belongs to one session id, with one configuration, until the last agent holding it
lets go. The store is the same node-wide claim directory the ESP pairs use -- a directory per
key, one file per claim, no file ever rewriting another user's.

What this does NOT do is make the declaration authoritative: the first agent to claim a free VNI
still defines it. It makes it CONSISTENT, which is what stops one session's declaration from
reaching into another's data plane.
"""

from __future__ import annotations

import hashlib
import logging
from collections.abc import AsyncIterator, Collection, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from ai.backend.agent.network.pair_journal import PairJournal
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

DEFAULT_VNI_REGISTRY_DIR: Final = Path("/var/lib/backend.ai/net-vni")
#: Separates the session id from the configuration digest inside one claim. Neither half contains
#: it, and the claim name is already split on "~" by the store beneath.
_DIGEST_SEP: Final = "#"
#: The configuration fields a session's data plane is actually built from. Anything not here does
#: not change what the devices are, so re-declaring it is not a conflict.
_BOUND_FIELDS: Final = ("backend", "subnet", "vni", "mtu", "vxlan_port", "encryption_key")


def vni_key(vni: int) -> str:
    return f"vni{vni}"


def config_digest(raw_config: Mapping[str, Any]) -> str:
    """A short, stable fingerprint of what the session's devices are built from.

    Not a secret and not a signature -- an agent that can declare a configuration can compute its
    digest. It answers one question: is this the SAME declaration the VNI is already bound to?
    """
    parts = "|".join(f"{field}={raw_config.get(field)!r}" for field in _BOUND_FIELDS)
    return hashlib.sha256(parts.encode()).hexdigest()[:16]


@dataclass(frozen=True)
class VniHolder:
    """One agent's claim on a VNI: which agent, for which session, under which configuration."""

    agent_id: str
    session_id: str
    digest: str

    @classmethod
    def parse(cls, entry: str) -> VniHolder | None:
        owner, _, rest = entry.partition("/")
        session_id, _, digest = rest.rpartition(_DIGEST_SEP)
        if not owner or not session_id or not digest:
            return None
        return cls(agent_id=owner, session_id=session_id, digest=digest)


@dataclass(frozen=True)
class Binding:
    """The outcome of asking for a VNI, decided under the node-wide lock."""

    #: Whether this agent's claim reached the store. False means refuse: a binding no other agent
    #: can read is not one.
    recorded: bool
    #: Whether this VNI was ALREADY bound to this session before we asked -- by this agent or a
    #: co-located one. The caller must then adopt the existing data plane rather than build it:
    #: building deletes the devices first, and they are carrying that session's containers.
    already_held: bool


class VniConflict(Exception):
    """The VNI is already bound to a different session, or to a different configuration."""


class VniRegistry:
    """Node-wide VNI -> (session, configuration) bindings."""

    _journal: PairJournal

    def __init__(self, root: Path | None = None) -> None:
        # Read through the module attribute rather than a default argument, so a test can redirect
        # the node-global path -- the same reason `PairJournal` does.
        self._journal = PairJournal(root if root is not None else DEFAULT_VNI_REGISTRY_DIR)

    def unusable_reason(self) -> str | None:
        return self._journal.unusable_reason()

    async def holders(self, vni: int) -> frozenset[VniHolder]:
        """Everyone on this node currently bound to the VNI, for diagnostics and refusal text."""
        return frozenset(
            holder
            for entry in await self._journal.users(vni_key(vni))
            if (holder := VniHolder.parse(entry)) is not None
        )

    @asynccontextmanager
    async def binding(
        self, vni: int, owner: str, session_id: str, digest: str
    ) -> AsyncIterator[Binding]:
        """Bind the VNI to this session and hold the node-wide lock across the caller's block.

        One step, like the ESP pair claim it is built on: between deciding the VNI is free and
        building the devices there is a window in which another agent decides the same thing, and
        the two then build over each other.

        Yields what was decided -- see `Binding`. Both halves matter: whether we may proceed, and
        whether the data plane is already there and must be adopted rather than rebuilt.

        Raises `VniConflict` when the VNI is already another session's, or the same session's
        under a different configuration. Nothing is written in that case.
        """
        async with self._journal.holding(vni_key(vni)) as claims:
            if claims is None:
                yield Binding(recorded=False, already_held=False)
                return
            existing = claims.users()
            if existing is None:
                # Unlistable is not free. Answering "nobody holds it" here is what authorises
                # deleting the devices of whoever does.
                yield Binding(recorded=False, already_held=False)
                return
            already_held = False
            for entry in existing:
                holder = VniHolder.parse(entry)
                if holder is None:
                    continue
                if holder.session_id == session_id and holder.digest == digest:
                    already_held = True
                    continue
                raise VniConflict(
                    f"VNI {vni} on this node is already held by session {holder.session_id}"
                    f" (agent {holder.agent_id})"
                    + (
                        " under a different network configuration"
                        if holder.session_id == session_id
                        else ""
                    )
                )
            recorded = claims.add(owner, f"{session_id}{_DIGEST_SEP}{digest}")
            yield Binding(recorded=recorded, already_held=already_held)

    @asynccontextmanager
    async def releasing(
        self, vni: int, owner: str, session_id: str, digest: str
    ) -> AsyncIterator[bool | None]:
        """Drop this agent's binding, holding the lock across the caller's teardown.

        Yields whether the VNI is now free on this node: True, False, or None when that could not
        be determined -- which the caller must treat as "not free".
        """
        async with self._journal.releasing(
            vni_key(vni), owner, f"{session_id}{_DIGEST_SEP}{digest}"
        ) as freed:
            yield freed

    async def prune(self, owner: str, live: Collection[tuple[str, str]]) -> int:
        """Drop this agent's bindings for sessions it no longer has.

        A crash between binding a VNI and tearing it down leaves a binding nobody is behind, and
        the VNI it names is then refused to every later session on this node.
        """
        return await self._journal.prune(
            owner, [f"{session_id}{_DIGEST_SEP}{digest}" for session_id, digest in live]
        )
