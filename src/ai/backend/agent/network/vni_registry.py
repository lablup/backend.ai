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

from ai.backend.agent.network.pair_journal import ClaimSet, PairJournal
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

DEFAULT_VNI_REGISTRY_DIR: Final = Path("/var/lib/backend.ai/net-vni")
#: Separates the parts of one claim: state, session id and configuration digest. None of them
#: contains it, and the claim name is already split on "~" by the store beneath.
_SEP: Final = "#"
#: A VNI this agent has reserved but whose devices are not (yet) known to exist. It conflicts with
#: every other session exactly as a built one does -- two agents must not build the same VNI -- but
#: it is NOT an existing data plane, and adopting one adopts nothing.
_HELD: Final = "held"
#: A VNI whose devices this agent actually built. Only this state means "already there": a setup
#: that failed after claiming, and failed to clean up after itself, otherwise made the next setup
#: adopt a data plane that was never finished.
_BUILT: Final = "built"
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


def _claim_id(state: str, session_id: str, digest: str) -> str:
    return f"{state}{_SEP}{session_id}{_SEP}{digest}"


@dataclass(frozen=True)
class VniHolder:
    """One agent's claim on a VNI: which agent, for which session, under which configuration, and
    whether that session's devices are known to exist."""

    agent_id: str
    session_id: str
    digest: str
    built: bool

    @classmethod
    def parse(cls, entry: str) -> VniHolder | None:
        owner, _, rest = entry.partition("/")
        state, _, remainder = rest.partition(_SEP)
        session_id, _, digest = remainder.rpartition(_SEP)
        if not owner or state not in (_HELD, _BUILT) or not session_id or not digest:
            return None
        return cls(agent_id=owner, session_id=session_id, digest=digest, built=state == _BUILT)


@dataclass(frozen=True)
class Binding:
    """The outcome of asking for a VNI, and the handle for saying how it turned out.

    Live for the caller's block only: every method here writes under the node-wide lock the
    `binding` context manager is holding, and does nothing once it has been left.
    """

    #: Whether this agent's claim reached the store. False means refuse: a binding no other agent
    #: can read is not one.
    recorded: bool
    #: Whether this session's data plane is ALREADY BUILT on this host -- by this agent before a
    #: restart, or by a co-located one. The caller must then adopt it rather than build it:
    #: building deletes the devices first, and they are carrying that session's containers.
    #:
    #: A reservation alone is deliberately not enough. The claim is written BEFORE the devices, so
    #: a setup that died in the middle leaves one behind, and treating it as "already there" makes
    #: the next setup adopt a data plane that was never finished.
    already_held: bool

    _claims: ClaimSet | None = None
    _owner: str = ""
    _session_id: str = ""
    _digest: str = ""

    def mark_built(self) -> bool:
        """Record that this session's devices now exist, so a later setup adopts them."""
        if self._claims is None:
            return False
        if not self._claims.add(self._owner, _claim_id(_BUILT, self._session_id, self._digest)):
            return False
        return self._claims.remove(self._owner, _claim_id(_HELD, self._session_id, self._digest))

    def abandon(self) -> None:
        """Give the reservation back after a build that did not happen.

        Leaving it costs the VNI: nothing on this node may use it until the next restart prunes
        it. Safe rather than correct is still not correct.
        """
        if self._claims is None:
            return
        self._claims.remove(self._owner, _claim_id(_HELD, self._session_id, self._digest))


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
                    already_held = already_held or holder.built
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
            state = _BUILT if already_held else _HELD
            recorded = claims.add(owner, _claim_id(state, session_id, digest))
            yield Binding(
                recorded=recorded,
                already_held=already_held,
                _claims=claims,
                _owner=owner,
                _session_id=session_id,
                _digest=digest,
            )

    @asynccontextmanager
    async def releasing(
        self, vni: int, owner: str, session_id: str, digest: str
    ) -> AsyncIterator[bool | None]:
        """Drop this agent's binding, holding the lock across the caller's teardown.

        Yields whether the VNI is now free on this node -- meaning the caller may DELETE its
        devices. True, False, or None when it could not be determined, which the caller must treat
        as "not free": deleting a shared bridge on a guess cuts a co-located agent's containers
        off the network, and its own locator cannot even see them.

        The lock spans the caller's block, so the answer cannot go stale between being given and
        being acted on.
        """
        async with self._journal.holding(vni_key(vni)) as claims:
            if claims is None:
                yield None
                return
            # Both states: which one this agent left behind depends on whether its build finished.
            dropped = claims.remove(owner, _claim_id(_BUILT, session_id, digest))
            dropped = claims.remove(owner, _claim_id(_HELD, session_id, digest)) and dropped
            if not dropped:
                yield None
                return
            remaining = claims.users()
            yield None if remaining is None else not remaining

    async def prune(self, owner: str, live: Collection[tuple[str, str]]) -> int:
        """Drop this agent's bindings for sessions it no longer has.

        A crash between binding a VNI and tearing it down leaves a binding nobody is behind, and
        the VNI it names is then refused to every later session on this node.
        """
        return await self._journal.prune(
            owner,
            [
                _claim_id(state, session_id, digest)
                for session_id, digest in live
                for state in (_HELD, _BUILT)
            ],
        )
