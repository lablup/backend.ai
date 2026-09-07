"""Conflict-safe IPAM/VNI allocation for cluster-session networks.

Allocation state lives in etcd under ``network/ipam/*`` and is claimed with
``AsyncEtcd.put_if_absent`` (a compare-and-swap on ``create_revision == 0``),
replacing Swarm's internal global IPAM. See BEP-1078 (control plane).
"""

from __future__ import annotations

import asyncio
import ipaddress
import json
import logging
import secrets
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any
from urllib.parse import quote, unquote

from ai.backend.common.network.keys import (
    endpoint_key,
    session_ipam_key,
    session_ipam_prefix,
)
from ai.backend.common.network.types import (
    DEFAULT_VNI_RANGE,
    SESSION_META_GENERATION,
    EndpointAddr,
    mac_for_ip,
    of_generation,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.errors.network import (
    EndpointSuperseded,
    NetworkPoolExhausted,
    RequestedSubnetInvalid,
    RequestedSubnetUnavailable,
    SubnetClaimStranded,
    VNIPoolExhausted,
)

if TYPE_CHECKING:
    from ai.backend.common.etcd import AsyncEtcd

DEFAULT_IPAM_POOL = "10.128.0.0/12"
DEFAULT_BLOCK_PREFIXLEN = 24

#: How many times `EndpointAllocator.assign` re-reads an endpoint record that changed under its
#: compare-and-swap before it gives up. More than one because a concurrent create of the SAME
#: incarnation writes the same values and is not a conflict; bounded because a record that will not
#: settle is a caller's retry, not a loop to spin in.
_SETTLE_ATTEMPTS = 3

_ALLOCATED_PREFIX = "network/ipam/allocated"
_VNI_PREFIX = "network/ipam/vni"
_OVERLAY_KEY = "network/overlay-encryption-key"

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


def _prefix_for_hosts(host_count: int, *, default_prefixlen: int, floor_prefixlen: int) -> int:
    """Smallest block (largest prefix) that holds ``host_count`` usable addresses.

    A fixed ``/24`` caps a session at 254 endpoints; a larger cluster needs a bigger
    block. Starts at ``default_prefixlen`` (``/24``) and widens (lowers the prefix) until
    the block is big enough, bounded by ``floor_prefixlen`` (the pool's own prefix).
    """
    prefixlen = default_prefixlen
    while prefixlen > floor_prefixlen and ((1 << (32 - prefixlen)) - 2) < max(host_count, 1):
        prefixlen -= 1
    return prefixlen


def _allocated_key(cidr: str) -> str:
    return f"{_ALLOCATED_PREFIX}/{quote(cidr, safe='')}"


def _flat(listing: Mapping[str, Any]) -> dict[str, str]:
    """A prefix listing reduced to its leaf values. A key holding children, not a value, is
    not a claim and is dropped."""
    return {key: value for key, value in listing.items() if isinstance(value, str)}


def _own_vni(allocated: Mapping[str, str], session_id: str, generation: str | None) -> int | None:
    """The VNI this session already holds, out of a listing of every claim.

    Matched on the owner and the incarnation rather than the exact payload: a claim a previous
    attempt stranded carries no generation (or this one), and taking a SECOND VNI beside it leaves
    the first held by an attempt nothing will come back for. A claim stamped with a different
    incarnation is not this session's to adopt.
    """
    for key, raw in allocated.items():
        if not key.isdigit():
            continue
        try:
            if json.loads(raw).get("session_id") != session_id:
                continue
        except ValueError:
            continue
        if of_generation(raw, generation):
            return int(key)
    return None


def _claim(session_id: str, subnet: str, generation: str | None = None) -> str:
    """The value stored on every unit block of ``subnet``.

    It carries the whole block, not just the owner, so the session's existing allocation can be
    recovered from any one of its units -- which is what makes ``acquire`` idempotent. It carries
    the generation for the opposite reason: the session id is reused, so the owner alone does not
    say WHICH incarnation of it holds the block, and a release that could not tell them apart gave
    a live session's block back to the pool (see `of_generation`).

    The generation is left out of the payload when there is none, so a claim written by a manager
    from before the field and one written without it are the same bytes.
    """
    claim: dict[str, str] = {"session_id": session_id, "subnet": subnet}
    if generation is not None:
        claim[SESSION_META_GENERATION] = generation
    return json.dumps(claim)


def _vni_claim(session_id: str, generation: str | None = None) -> str:
    """The value stored on an allocated VNI key. Shaped like `_claim`, and for the same reasons."""
    claim: dict[str, str] = {"session_id": session_id}
    if generation is not None:
        claim[SESSION_META_GENERATION] = generation
    return json.dumps(claim)


def _endpoint_claim(container_id: str, generation: str | None = None) -> str:
    """The value stored on a per-session address reservation. Shaped like `_claim`."""
    claim: dict[str, str] = {"container_id": container_id}
    if generation is not None:
        claim[SESSION_META_GENERATION] = generation
    return json.dumps(claim)


def _claimed_subnet(raw: str, session_id: str, generation: str | None) -> str | None:
    """The block ``raw`` records, if it is this INCARNATION of this session's claim.

    The session id alone is not ownership. A session id is reused, and a claim an earlier
    incarnation made is released by that incarnation's cleanup -- so a later one that adopted it
    on the strength of the id would be running on a block the pool has since handed to somebody
    else. Two live sessions on one subnet is not a leak; it is two tenants at the same addresses.

    A claim carrying no generation at all is adopted by any: that is what a manager from before
    the field wrote, and nothing else will come back for it.
    """
    try:
        claim = json.loads(raw)
    except ValueError:
        return None
    if claim.get("session_id") != session_id:
        return None
    if not of_generation(raw, generation):
        return None
    subnet = claim.get("subnet")
    return str(subnet) if subnet else None


def _unit_blocks(
    subnet: ipaddress.IPv4Network | ipaddress.IPv6Network, unit_prefixlen: int
) -> list[str]:
    """The fixed-size unit blocks a session subnet is composed of.

    A session block is never narrower than ``unit_prefixlen`` (widening only lowers the prefix),
    so it tiles into ``2**(unit_prefixlen - subnet.prefixlen)`` contiguous unit blocks. Claiming
    the allocation at this fixed granularity — the way Docker's IPAM carves its pool into
    fixed-size subnets — is what lets a wider block collide (via CAS on a shared unit) with a
    narrower one it contains, instead of both succeeding on distinct exact-CIDR keys and
    overlapping. ``unit_prefixlen`` clamps up to ``subnet.prefixlen`` for a subnet that is already
    at (or below) unit size, which yields the subnet itself as its sole unit.
    """
    new_prefix = max(unit_prefixlen, subnet.prefixlen)
    return [str(unit) for unit in subnet.subnets(new_prefix=new_prefix)]


class SubnetAllocator:
    """Allocates per-session subnets from a pool using etcd CAS."""

    _etcd: AsyncEtcd
    _pool: str
    _block_prefixlen: int

    def __init__(
        self,
        etcd: AsyncEtcd,
        *,
        pool: str = DEFAULT_IPAM_POOL,
        block_prefixlen: int = DEFAULT_BLOCK_PREFIXLEN,
    ) -> None:
        self._etcd = etcd
        self._pool = pool
        self._block_prefixlen = block_prefixlen

    async def acquire(
        self,
        session_id: str,
        *,
        host_count: int = 1,
        subnet: str | None = None,
        generation: str | None = None,
    ) -> str:
        """Claim a session subnet via CAS and return its CIDR.

        Two modes, mirroring ``docker network create``:

        - **Auto** (``subnet is None``): claim the first free block sized for ``host_count``
          endpoints (``host_count`` = total containers), removing the fixed-``/24`` 254-endpoint
          ceiling. ``host_count=1`` yields the default ``/24``. An overlapping/taken block is
          skipped for the next candidate.
        - **Explicit** (``subnet`` given, like ``--subnet``): claim exactly that block. An overlap
          is a hard failure, not a relocation, and ``host_count`` is ignored (the request already
          fixed the size).

        Either way the block is registered as its fixed-size *unit* blocks (``block_prefixlen``),
        not as a single variable-width key: a wider block and a narrower one that overlaps it share
        a unit, so the CAS on that unit rejects the overlap. A block only partially claimed (a later
        unit was already taken) is fully released before the mode's failure/skip, so it is never
        split between two sessions.

        ``generation`` stamps the claim with the incarnation of ``session_id`` making it, so a
        later cleanup can tell this allocation from the one a session started again under the same
        id holds (see `_claim`).

        Raises:
            NetworkPoolExhausted: auto mode, no free block of the required size remains.
            RequestedSubnetInvalid: explicit mode, the subnet is malformed, unaligned, outside the
                pool, or narrower than one unit block.
            RequestedSubnetUnavailable: explicit mode, the subnet overlaps an allocated block.
        """
        pool = ipaddress.ip_network(self._pool)
        taken = _flat(await self._etcd.get_prefix(_ALLOCATED_PREFIX))
        if held := self._already_held(taken, session_id, generation):
            return held
        # A block this session holds only part of: an acquire that died between its units. Finish
        # it, or give the part back so the pool is not carrying a claim nobody can use.
        if (
            finished := await self._finish_partial_claim(taken, session_id, generation)
        ) is not None:
            return finished
        if subnet is not None:
            return await self._acquire_requested(subnet, pool, session_id, generation)
        prefixlen = _prefix_for_hosts(
            host_count,
            default_prefixlen=self._block_prefixlen,
            floor_prefixlen=pool.prefixlen,
        )
        owned = {unquote(key) for key in taken}
        for candidate in pool.subnets(new_prefix=prefixlen):
            units = _unit_blocks(candidate, self._block_prefixlen)
            # The listing is a snapshot, so it can only rule a candidate OUT; a candidate it
            # says is free still has to win the CAS below. Reading it first is what keeps a
            # pool with many live sessions from paying one round trip per taken block.
            if any(unit in owned for unit in units):
                continue
            if await self._try_claim_units(
                candidate, _claim(session_id, str(candidate), generation)
            ):
                return str(candidate)
            # Lost the compare-and-swap. The winner can be this very session -- a second manager
            # creating it at the same time -- and moving to the next block would then leave one
            # of the two claimed by nobody's meta, for the cluster's lifetime. Ask again who
            # holds what before deciding this candidate is somebody else's.
            taken = _flat(await self._etcd.get_prefix(_ALLOCATED_PREFIX))
            if held := self._already_held(taken, session_id, generation):
                return held
            owned = {unquote(key) for key in taken} | set(units)
        raise NetworkPoolExhausted()

    def _already_held(
        self, allocated: Mapping[str, str], session_id: str, generation: str | None
    ) -> str | None:
        """The block this session already owns *whole*, if a previous ``acquire`` got that far.

        The caller retries a failed session start with the same id, and a create that was
        cancelled or died between the claim and the session's meta record leaves the block
        claimed with nobody to release it. Handing back the same block makes the retry converge
        instead of claiming a second one and orphaning the first.

        Whole, because a block wider than one unit is claimed a unit at a time. Answering on the
        strength of one of them would hand back a ``/23`` whose second half nothing holds -- and
        the pool would give that half to the next session, overlapping the address space of one
        that believes it has the lot. A partial claim is reported through `_partly_held` instead,
        for the caller to finish or give up.
        """
        for held in self._claims_of(allocated, session_id, generation):
            units = self._units_of(held)
            if len(self._ours_among(allocated, units, session_id, generation)) == len(units):
                return held
        return None

    def _claims_of(
        self, allocated: Mapping[str, str], session_id: str, generation: str | None
    ) -> list[str]:
        """Every distinct block this incarnation has a unit claimed for, widest first."""
        blocks = {
            held
            for raw in allocated.values()
            if (held := _claimed_subnet(raw, session_id, generation))
        }
        return sorted(blocks, key=lambda block: ipaddress.ip_network(block).prefixlen)

    def _units_of(self, subnet: str) -> list[str]:
        return _unit_blocks(ipaddress.ip_network(subnet), self._block_prefixlen)

    @staticmethod
    def _ours_among(
        allocated: Mapping[str, str],
        units: Sequence[str],
        session_id: str,
        generation: str | None,
    ) -> list[str]:
        """Which of ``units`` this incarnation holds. Presence is not enough -- a unit another
        session, or another incarnation of this one, took is exactly what makes a block not
        ours."""
        return [
            unit
            for unit in units
            if _claimed_subnet(allocated.get(quote(unit, safe=""), ""), session_id, generation)
            is not None
        ]

    async def _finish_partial_claim(
        self, allocated: Mapping[str, str], session_id: str, generation: str | None = None
    ) -> str | None:
        """Complete a block this session holds only part of, or give the part back.

        A wide block is claimed a unit at a time, so an acquire that died partway leaves one.
        Finishing it is what the retry wants; if somebody else has taken a unit in the meantime
        the block can never be this session's, and holding the rest of it helps nobody.
        """
        for block in self._claims_of(allocated, session_id, generation):
            units = self._units_of(block)
            ours = self._ours_among(allocated, units, session_id, generation)
            if len(ours) == len(units):
                continue  # whole; `_already_held` deals with it
            payload = _claim(session_id, block, generation)
            missing = [unit for unit in units if unit not in ours]
            won = list(ours)
            for unit in missing:
                if await self._etcd.put_if_absent(_allocated_key(unit), payload):
                    won.append(unit)
                    continue
                # Somebody else holds a piece of it. This block is not this session's to have.
                log.warning(
                    "giving back session {}'s partial claim on {}: another session holds {}",
                    session_id,
                    block,
                    unit,
                )
                if stuck := await self._give_back(won, payload):
                    raise SubnetClaimStranded(
                        f"could not give back session {session_id}'s partial claim on {block}"
                        f" ({', '.join(stuck)}); the pool cannot be accounted for"
                    )
                return None
            log.info("completed session {}'s partial claim on {}", session_id, block)
            return block
        return None

    async def _acquire_requested(
        self,
        subnet: str,
        pool: ipaddress.IPv4Network | ipaddress.IPv6Network,
        session_id: str,
        generation: str | None = None,
    ) -> str:
        """Claim an explicitly requested block, validating it against the pool first."""
        try:
            # strict=True rejects a subnet whose host bits are set, i.e. one not aligned to its
            # own prefix (e.g. 10.128.1.0/23) — the same misalignment Docker's IPAM rejects.
            requested = ipaddress.ip_network(subnet, strict=True)
        except ValueError as e:
            raise RequestedSubnetInvalid(
                f"'{subnet}' is not a valid, prefix-aligned subnet: {e}"
            ) from e
        # `subnet_of` is typed per address family and refuses a mixed pair, which is the same
        # thing the version check above is for -- so tell the checker they match by narrowing to
        # one family rather than asserting the comparison is fine.
        contained = (
            isinstance(requested, ipaddress.IPv4Network)
            and isinstance(pool, ipaddress.IPv4Network)
            and requested.subnet_of(pool)
        ) or (
            isinstance(requested, ipaddress.IPv6Network)
            and isinstance(pool, ipaddress.IPv6Network)
            and requested.subnet_of(pool)
        )
        if not contained:
            raise RequestedSubnetInvalid(f"'{requested}' is not contained in the IPAM pool {pool}.")
        if requested.prefixlen > self._block_prefixlen:
            raise RequestedSubnetInvalid(
                f"'{requested}' is narrower than one unit block (/{self._block_prefixlen}); the pool"
                " is accounted at that granularity. Lower ipam-block-size to request a smaller block."
            )
        if not await self._try_claim_units(
            requested, _claim(session_id, str(requested), generation)
        ):
            # As in auto mode: the winner may be this same session, and that is not a conflict.
            taken = _flat(await self._etcd.get_prefix(_ALLOCATED_PREFIX))
            if (held := self._already_held(taken, session_id, generation)) == str(requested):
                return held
            raise RequestedSubnetUnavailable(
                f"'{requested}' overlaps a subnet already allocated to another session."
            )
        return str(requested)

    async def _try_claim_units(
        self,
        candidate: ipaddress.IPv4Network | ipaddress.IPv6Network,
        payload: str,
    ) -> bool:
        """CAS-claim every unit block of ``candidate``; return False (and give back any partial
        claim) if any unit is already owned, so the block is never split between two sessions.

        The partial claim is given back on *any* way out, not only on a unit that was taken: a
        cancelled or failed acquire that walked away from the units it had already won would leave
        a block that is half this session's and half free -- and the free half is what the next
        session is handed, overlapping the address space of a session that thinks it owns the
        whole block.
        """
        units = _unit_blocks(candidate, self._block_prefixlen)
        try:
            for unit in units:
                if await self._etcd.put_if_absent(_allocated_key(unit), payload):
                    continue
                # Fail, rather than move on to the next block: a unit that would not go back is
                # named by no meta and released by nothing, so carrying on would report a healthy
                # session over a pool that has silently shrunk.
                if stuck := await self._give_back(units, payload):
                    raise SubnetClaimStranded(
                        f"could not give back the partial claim {payload} on"
                        f" {', '.join(stuck)}; the pool cannot be accounted for"
                    )
                return False
        except BaseException:
            # Best-effort here and nothing more: this is the cancelled/failed path, and raising
            # over it would replace the failure being unwound.
            await asyncio.shield(asyncio.ensure_future(self._give_back(units, payload)))
            raise
        return True

    async def _give_back(self, units: Sequence[str], payload: str) -> list[str]:
        """Release every unit of a block this claim owns; return the ones that would not go back.

        Every unit, rather than the ones the loop recorded: a claim whose compare-and-swap
        committed and whose answer never came back is held by this session and named in no list.
        """
        stuck: list[str] = []
        for unit in units:
            try:
                await self._etcd.delete_if_value(_allocated_key(unit), payload)
            except Exception:
                # Kept going, not raised: the remaining units are worth more than the first
                # failure, and the caller decides what an incomplete give-back means.
                stuck.append(unit)
        if stuck:
            log.error(
                "could not give back {} unit block(s) of a partial claim: {}. They stay claimed"
                " by {} and no later release names them.",
                len(stuck),
                ", ".join(stuck),
                payload,
            )
        return stuck

    async def release_all(self, session_id: str, generation: str | None = None) -> list[str]:
        """Give back every unit block this INCARNATION of the session claimed, whatever any meta
        says.

        The claim names the session, so this reaches what a record never got to name: a create
        cancelled between the claim and its publish, and a partial claim that would not go back.

        It names the incarnation too, and that is what keeps a slow cleanup out of a live session:
        the block a session started again under the same id holds is this session's by every name
        the pool records, and a cleanup that could not tell the two apart handed it back to the
        pool while its containers were running on it. A claim stamped with another generation is
        left where it is (see `of_generation`).
        """
        payload_of = {}
        for key, raw in _flat(await self._etcd.get_prefix(_ALLOCATED_PREFIX)).items():
            if _claimed_subnet(raw, session_id, generation) is not None:
                payload_of[unquote(key)] = raw
        stuck: list[str] = []
        for unit, payload in payload_of.items():
            try:
                await self._etcd.delete_if_value(_allocated_key(unit), payload)
            except Exception:
                stuck.append(unit)
        if stuck:
            log.error(
                "could not give back {} unit block(s) of session {}: {}",
                len(stuck),
                session_id,
                ", ".join(sorted(stuck)),
            )
        return stuck

    async def holder(self, subnet: str) -> str | None:
        """The session every unit block of ``subnet`` is claimed by, or None if they disagree or
        any of them is free. Used to tell a live allocation from a record that outlived one."""
        owners: set[str] = set()
        for unit in _unit_blocks(ipaddress.ip_network(subnet), self._block_prefixlen):
            raw = await self._etcd.get(_allocated_key(unit))
            if not isinstance(raw, str):
                return None
            try:
                owners.add(str(json.loads(raw)["session_id"]))
            except (ValueError, KeyError):
                return None
        return owners.pop() if len(owners) == 1 else None

    async def release(self, subnet: str, session_id: str, generation: str | None = None) -> bool:
        """Give the subnet back, but only the unit blocks this session still owns.

        Same reasoning as `VniAllocator.release`: the pool is shared, so releasing a block that
        now belongs to somebody else is what lets two sessions be handed overlapping overlay
        address space.

        ``generation`` narrows it further to one incarnation of the session; without one, any
        claim this session holds on the block is released. Either way the delete names the exact
        bytes read, so a claim rewritten under this call is left where it is.

        :return: ``True`` if every unit block was still this session's.
        """
        released = True
        for unit in _unit_blocks(ipaddress.ip_network(subnet), self._block_prefixlen):
            raw = await self._etcd.get(_allocated_key(unit))
            if not isinstance(raw, str) or _claimed_subnet(raw, session_id, generation) != subnet:
                released = False
                continue
            if not await self._etcd.delete_if_value(_allocated_key(unit), raw):
                released = False
        return released


class EndpointAllocator:
    """Assigns a per-endpoint overlay ``{ip, mac}`` centrally, via etcd CAS.

    Central assignment (vs per-node host-local IPAM) is what guarantees disjoint IPs
    across nodes on a stretched overlay subnet; the written ``endpoints/`` table is also
    the input the agent coordinator uses to program FDB/ARP proactively. See
    BEP-1078 (control plane).
    """

    _etcd: AsyncEtcd

    def __init__(self, etcd: AsyncEtcd) -> None:
        self._etcd = etcd

    async def assign(
        self,
        session_id: str,
        container_id: str,
        subnet: str,
        *,
        agent_id: str,
        cluster_hostname: str | None = None,
        generation: str | None = None,
        guards: Mapping[str, str] | None = None,
    ) -> tuple[str, str]:
        """Claim the first free host IP in ``subnet`` for ``container_id`` (placed on
        ``agent_id``) and record the endpoint. Returns ``(ip, mac)``.

        ``agent_id`` is stored so a peer coordinator can resolve the endpoint's VTEP and
        skip its own local endpoints when programming FDB/ARP. ``cluster_hostname`` is stored
        so the per-session cluster name resolver can answer ``hostname -> ip`` from this same
        table (BEP-1078, cluster-name-resolution.md).

        An address this container already holds is returned as it stands: a retried session
        start must not hand the same container a second address and strand the first.

        ``generation`` stamps both the address reservation and the endpoint record with the
        incarnation of ``session_id`` they belong to, so a cleanup of the previous one cannot
        delete them (see `_claim`).

        ``guards`` are keys that must still hold exactly the bytes given -- in practice the
        session's own record, as the caller holds it. Every write below is conditional on them in
        the SAME store operation, because the generation stamp alone cannot stop a write that
        CREATES a key: a stale create finding the address free is finding it free because the
        session it belongs to was torn down, and stamping the key it then makes does not make the
        key legitimate. What it writes must be refused, not merely labelled.

        Raises:
            NetworkPoolExhausted: the session subnet has no free host address.
            EndpointSuperseded: the session record moved on, or the endpoint belongs to a later
                incarnation.
        """
        claim = _endpoint_claim(container_id, generation)
        guards = dict(guards or {})

        async def settle(ip: str) -> tuple[str, str]:
            """Make the endpoint record say what the address claim already says.

            The address and the record are two writes, and everything downstream reads the
            record: peers program FDB and ARP from it, and the cluster resolver answers from it.
            A container holding an address that no record mentions is a kernel the rest of the
            session cannot reach, on a session that reports itself healthy -- so the record is
            written here whether this call made the claim or found it.

            Written over nothing but this incarnation's own record. A create stalled across a
            teardown and a rebuild of the same session id resumes holding the old subnet, and an
            unconditional write here put its addresses under the LIVE session's container ids --
            which every peer then programs into its FDB and ARP. There is no lock to hold across
            the two writes, so the fence is the record itself: only bytes carrying this
            incarnation's generation are replaced, and only by compare-and-swap.

            Raises:
                EndpointSuperseded: the record belongs to another incarnation of the session.
            """
            mac = mac_for_ip(ip)
            payload = json.dumps(
                EndpointAddr(
                    container_id=container_id,
                    ip=ip,
                    mac=mac,
                    agent_id=agent_id,
                    cluster_hostname=cluster_hostname,
                    generation=generation,
                ).to_etcd_payload()
            )
            key = endpoint_key(session_id, container_id)
            for _ in range(_SETTLE_ATTEMPTS):
                standing = await self._etcd.get(key)
                if standing == payload:
                    return ip, mac
                if standing is not None and not of_generation(standing, generation):
                    raise EndpointSuperseded(
                        f"session {session_id}'s endpoint record for container {container_id}"
                        " belongs to a later incarnation of the session; not writing this"
                        " create's addresses over the one its peers are using"
                    )
                if await self._etcd.compare_and_put(key, payload, expected=standing, guards=guards):
                    return ip, mac
            raise EndpointSuperseded(
                f"session {session_id}'s endpoint record for container {container_id} could not be"
                f" written under this create's own record ({_SETTLE_ATTEMPTS} attempts); the"
                " session has moved on, or the record kept changing"
            )

        held = _flat(await self._etcd.get_prefix(session_ipam_prefix(session_id)))
        for ip, raw in held.items():
            if raw == claim:
                return await settle(ip)
        taken = set(held)
        for host in ipaddress.ip_network(subnet).hosts():
            ip = str(host)
            if ip in taken:
                continue
            if await self._etcd.compare_and_put(
                session_ipam_key(session_id, ip), claim, expected=None, guards=guards
            ):
                return await settle(ip)
            # The write lost either because the address was taken under us or because the record
            # guarding it moved on. Told apart, because they mean opposite things: the first is
            # the next candidate address, the second is every candidate refused in turn -- a scan
            # of the whole subnet on behalf of a session that no longer exists.
            await self._require_guards(session_id, guards)
            # Lost the CAS. It can be this very container, claimed by a concurrent create of the
            # same session; taking a second address would strand the first.
            held = _flat(await self._etcd.get_prefix(session_ipam_prefix(session_id)))
            for other, raw in held.items():
                if raw == claim:
                    return await settle(other)
            taken = set(held) | {ip}
        raise NetworkPoolExhausted()

    async def _require_guards(self, session_id: str, guards: Mapping[str, str]) -> None:
        """Stop the assignment if what makes it legitimate is no longer there.

        Raises:
            EndpointSuperseded: a guard key no longer holds the bytes it was given for.
        """
        for key, expected in guards.items():
            if await self._etcd.get(key) != expected:
                raise EndpointSuperseded(
                    f"session {session_id}'s record changed while an address was being assigned"
                    " for it; not claiming one on behalf of a session that has moved on"
                )

    async def release(self, session_id: str, container_id: str, ip: str) -> None:
        await self._etcd.delete(session_ipam_key(session_id, ip))
        await self._etcd.delete(endpoint_key(session_id, container_id))


async def overlay_encryption_key(etcd: AsyncEtcd) -> str:
    """The cluster's overlay encryption secret, created once and reused.

    A root to derive from, not a key that reaches a kernel: each agent expands it into a key for one
    node pair and 12-hour generation (`ai.backend.agent.network.backends.vxlan._pair_key`), because
    `ip xfrm state` prints an SA's key back in the clear and this value protects every pair in the
    cluster.

    One secret for the whole cluster, not one per session — the same shape Docker Swarm uses, and the
    only shape the data plane can actually honour. ESP policies select on the OUTER packet (VTEP
    addresses and the VXLAN UDP port); the VNI that identifies a session lives inside that packet's
    payload, where no XFRM selector reaches it. So every session between a pair of nodes shares one
    policy no matter how many keys exist, and with per-session keys the kernel simply picks one of
    the matching SAs — measured: of two SAs on one policy, one carried every packet and the other
    none, and which one is not something either end chooses. A per-session key was therefore a
    promise the layer below could not keep.

    With one key the ambiguity is gone: whichever SA is used, it is the same secret. Session
    isolation on the overlay is the VNI's job (L2), as it is in Swarm.

    Created with put_if_absent so racing managers converge on one value. The root remains stable;
    agents derive previous/current/next traffic-key generations and rotate the XFRM SAs every 12
    hours. Automatic rotation of this etcd root itself remains a separate control-plane concern.
    """
    created = await etcd.put_if_absent(_OVERLAY_KEY, secrets.token_hex(32))
    if created:
        log.info("generated the cluster overlay encryption key")
    key = await etcd.get(_OVERLAY_KEY)
    if not key:
        raise RuntimeError("the overlay encryption key vanished from etcd right after it was set")
    return str(key)


class VNIAllocator:
    """Allocates VXLAN Network Identifiers; used only for the vxlan backend."""

    _etcd: AsyncEtcd
    _vni_range: tuple[int, int]

    def __init__(
        self,
        etcd: AsyncEtcd,
        *,
        vni_range: tuple[int, int] = DEFAULT_VNI_RANGE,
    ) -> None:
        self._etcd = etcd
        self._vni_range = vni_range

    async def acquire(self, session_id: str, generation: str | None = None) -> int:
        """Claim the first free VNI via CAS, or return the one this session already holds.

        A retried session start must land on the same VNI: claiming a second one strands the
        first, since only the VNI recorded in the session meta is ever released.

        Raises:
            VNIPoolExhausted: every VNI in the range is already allocated.
        """
        low, high = self._vni_range
        payload = _vni_claim(session_id, generation)
        allocated = _flat(await self._etcd.get_prefix(_VNI_PREFIX))
        if (mine := _own_vni(allocated, session_id, generation)) is not None:
            return mine
        # The listing only rules VNIs out -- it is a snapshot, so a VNI it shows as free still
        # has to be won by CAS. It saves a round trip per VNI already taken, which is what the
        # plain low-to-high scan costs once the pool has any depth of live sessions.
        taken = {int(key) for key in allocated if key.isdigit()}
        for vni in range(low, high + 1):
            if vni in taken:
                continue
            if await self._etcd.put_if_absent(f"{_VNI_PREFIX}/{vni}", payload):
                return vni
            # Same reasoning as the subnet allocator: a lost CAS whose winner is this session is
            # this session's VNI, not a reason to take a second one.
            allocated = _flat(await self._etcd.get_prefix(_VNI_PREFIX))
            if (mine := _own_vni(allocated, session_id, generation)) is not None:
                return mine
            taken = {int(key) for key in allocated if key.isdigit()}
        raise VNIPoolExhausted()

    async def release_all(self, session_id: str, generation: str | None = None) -> list[int]:
        """Give back every VNI this INCARNATION of the session claimed, whatever any meta says.

        The counterpart of `SubnetAllocator.release_all`, and there for the same two cases: a claim
        the record that should have named it never reached, and a live session that happens to
        share this one's id.
        """
        stuck: list[int] = []
        for key, raw in _flat(await self._etcd.get_prefix(_VNI_PREFIX)).items():
            if not key.isdigit():
                continue
            try:
                if json.loads(raw).get("session_id") != session_id:
                    continue
            except ValueError:
                continue
            if not of_generation(raw, generation):
                log.info(
                    "leaving vni {} claimed: it is held by another incarnation of session {}",
                    key,
                    session_id,
                )
                continue
            try:
                await self._etcd.delete_if_value(f"{_VNI_PREFIX}/{key}", raw)
            except Exception:
                stuck.append(int(key))
        if stuck:
            log.error(
                "could not give back {} VNI(s) of session {}: {}",
                len(stuck),
                session_id,
                ", ".join(str(vni) for vni in sorted(stuck)),
            )
        return stuck

    async def holder(self, vni: int) -> str | None:
        """The session ``vni`` is claimed by, or None if it is free."""
        raw = await self._etcd.get(f"{_VNI_PREFIX}/{vni}")
        if not isinstance(raw, str):
            return None
        try:
            return str(json.loads(raw)["session_id"])
        except (ValueError, KeyError):
            return None

    async def release(self, vni: int, session_id: str, generation: str | None = None) -> bool:
        """Give the VNI back, but only while it is still this session's.

        An unconditional delete releases whatever holds the key NOW. After a reuse that is the
        next session's claim, and dropping it hands the same VNI to a third: two live sessions
        then share one VNI, and either one's teardown removes the other's rules and devices.
        The claim records its owner, so the release can check it.

        ``generation`` names the incarnation whose claim this is; the same rule as everywhere
        else (`of_generation`). The delete names the exact bytes read, so a claim rewritten under
        this call is left where it is.

        :return: ``True`` if this incarnation still held it and it was released.
        """
        raw = await self._etcd.get(f"{_VNI_PREFIX}/{vni}")
        if not isinstance(raw, str):
            return False
        try:
            if json.loads(raw).get("session_id") != session_id:
                return False
        except ValueError:
            return False
        if not of_generation(raw, generation):
            return False
        return await self._etcd.delete_if_value(f"{_VNI_PREFIX}/{vni}", raw)
