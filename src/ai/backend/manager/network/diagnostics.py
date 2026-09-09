from __future__ import annotations

import json
import secrets
import time
from collections import OrderedDict
from dataclasses import dataclass
from urllib.parse import quote, unquote

from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.network.keys import session_meta_key
from ai.backend.common.network.types import (
    GenerationMatch,
    generation_match,
    reads_as_overlay_subnet,
    reads_as_vni,
)
from ai.backend.manager.errors.network import NetworkStateQuarantineFailed
from ai.backend.manager.network.cni import (
    CNINetworkPlugin,
    _AllocationState,
    _claim_is_live,
    _generation_of,
    _parse_allocation,
    _record,
)
from ai.backend.manager.network.ipam import EndpointAllocator, SubnetAllocator, VNIAllocator

_SESSION_ROOT = "network/session/"
_SUBNET_ROOT = "network/ipam/allocated/"
_VNI_ROOT = "network/ipam/vni/"
_AUDIT_SAMPLE_LIMIT = 20
_AUDIT_CACHE_SIZE = 4096


@dataclass(frozen=True)
class NetworkStateAudit:
    session_records: int
    pool_claims: int
    session_child_records: int
    invalid_records: int
    orphan_claims: int
    orphan_session_children: int
    samples: tuple[str, ...]

    @property
    def healthy(self) -> bool:
        return not (self.invalid_records or self.orphan_claims or self.orphan_session_children)


async def audit_overlay_state(etcd: AsyncEtcd) -> NetworkStateAudit:
    """Read all overlay ownership records without changing them."""
    sessions = 0
    pool_claims = 0
    children = 0
    invalid = 0
    orphan_claims = 0
    orphan_children = 0
    samples: list[str] = []
    cached_meta: OrderedDict[str, str | None] = OrderedDict()

    def sample(kind: str, key: str) -> None:
        if len(samples) < _AUDIT_SAMPLE_LIMIT:
            samples.append(f"{kind}:{key}")

    async def meta_of(session_id: str) -> str | None:
        if session_id in cached_meta:
            raw = cached_meta.pop(session_id)
            cached_meta[session_id] = raw
            return raw
        raw = await etcd.get(session_meta_key(session_id), scope=ConfigScopes.GLOBAL)
        cached_meta[session_id] = raw
        if len(cached_meta) > _AUDIT_CACHE_SIZE:
            cached_meta.popitem(last=False)
        return raw

    async for key, raw in etcd.iter_prefix("network/session", scope=ConfigScopes.GLOBAL):
        if not key.startswith(_SESSION_ROOT):
            continue
        relative = key[len(_SESSION_ROOT) :]
        parts = relative.split("/", 2)
        if len(parts) == 2 and parts[1] == "meta":
            sessions += 1
            if _parse_allocation(raw).state is _AllocationState.CORRUPT:
                invalid += 1
                sample("invalid-session", key)
            continue
        if len(parts) != 3 or parts[1] not in {"endpoints", "members", "ipam"}:
            invalid += 1
            sample("unknown-session-key", key)
            continue
        children += 1
        meta_raw = await meta_of(parts[0])
        if meta_raw is None:
            orphan_children += 1
            sample("orphan-session-child", key)
            continue
        live_generation = _generation_of(meta_raw)
        if live_generation is None:
            continue
        match = generation_match(raw, live_generation)
        if match is GenerationMatch.UNREADABLE:
            invalid += 1
            sample("invalid-session-child", key)
        elif match is GenerationMatch.DIFFERENT:
            orphan_children += 1
            sample("orphan-session-child", key)

    async def inspect_claim(key: str, raw: str, *, is_vni: bool) -> None:
        nonlocal invalid, orphan_claims, pool_claims
        pool_claims += 1
        claim = _record(raw)
        session_id = claim.get("session_id") if claim is not None else None
        if not isinstance(session_id, str) or not session_id:
            invalid += 1
            sample("invalid-pool-claim", key)
            return
        relative = key.removeprefix(_VNI_ROOT if is_vni else _SUBNET_ROOT)
        identity: str | int = relative
        if is_vni:
            try:
                identity = int(relative)
            except ValueError:
                invalid += 1
                sample("invalid-pool-key", key)
                return
        else:
            identity = unquote(relative)
        if not _claim_is_live(await meta_of(session_id), raw, is_vni, identity):
            orphan_claims += 1
            sample("orphan-pool-claim", key)

    async for key, raw in etcd.iter_prefix("network/ipam/allocated"):
        await inspect_claim(key, raw, is_vni=False)
    async for key, raw in etcd.iter_prefix("network/ipam/vni"):
        await inspect_claim(key, raw, is_vni=True)

    return NetworkStateAudit(
        session_records=sessions,
        pool_claims=pool_claims,
        session_child_records=children,
        invalid_records=invalid,
        orphan_claims=orphan_claims,
        orphan_session_children=orphan_children,
        samples=tuple(samples),
    )


async def repair_overlay_state(etcd: AsyncEtcd, *, pool: str, block_prefixlen: int) -> int:
    """Run the production reconciler once and return the number of reclaimed records."""
    plugin = CNINetworkPlugin(
        {},
        {
            "network": {
                "inter-container": {
                    "ipam-pool": pool,
                    "ipam-block-size": block_prefixlen,
                }
            }
        },
    )
    plugin._etcd = etcd
    plugin._subnet_allocator = SubnetAllocator(etcd, pool=pool, block_prefixlen=block_prefixlen)
    plugin._vni_allocator = VNIAllocator(etcd)
    plugin._endpoint_allocator = EndpointAllocator(etcd)
    return await plugin.reconcile_pool()


async def _quarantine_guards(etcd: AsyncEtcd, key: str, raw: str) -> dict[str, str | None]:
    if key.startswith((_SUBNET_ROOT, _VNI_ROOT)):
        is_vni = key.startswith(_VNI_ROOT)
        relative = key.removeprefix(_VNI_ROOT if is_vni else _SUBNET_ROOT)
        try:
            identity: str | int = int(relative) if is_vni else unquote(relative)
        except ValueError:
            return {}
        if (is_vni and reads_as_vni(identity) is None) or (
            not is_vni and reads_as_overlay_subnet(identity) is None
        ):
            return {}
        claim = _record(raw)
        session_id = claim.get("session_id") if claim is not None else None
        if not isinstance(session_id, str) or not session_id:
            raise NetworkStateQuarantineFailed(
                f"{key} has a valid pool identity but unreadable ownership"
            )
        meta_key = session_meta_key(session_id)
        meta_raw = await etcd.get(meta_key, scope=ConfigScopes.GLOBAL)
        if meta_raw is not None and _parse_allocation(meta_raw).state is _AllocationState.CORRUPT:
            raise NetworkStateQuarantineFailed(
                f"{key} cannot be judged while {meta_key} is unreadable"
            )
        if _claim_is_live(meta_raw, raw, is_vni, identity):
            raise NetworkStateQuarantineFailed(f"{key} is owned by a live session")
        return {meta_key: meta_raw}

    relative = key.removeprefix(_SESSION_ROOT)
    parts = relative.split("/", 2)
    if len(parts) != 3 or parts[1] not in {"endpoints", "members", "ipam"}:
        raise NetworkStateQuarantineFailed(f"{key} is not a session child record")
    meta_key = session_meta_key(parts[0])
    meta_raw = await etcd.get(meta_key, scope=ConfigScopes.GLOBAL)
    if meta_raw is None:
        return {meta_key: None}
    live_generation = _generation_of(meta_raw)
    if live_generation is None:
        raise NetworkStateQuarantineFailed(f"{key} cannot be judged while {meta_key} is unreadable")
    match = generation_match(raw, live_generation)
    if match is not GenerationMatch.DIFFERENT:
        raise NetworkStateQuarantineFailed(f"{key} is live or its ownership is unreadable")
    return {meta_key: meta_raw}


async def quarantine_overlay_record(etcd: AsyncEtcd, key: str) -> str:
    """Move one confirmed orphan to a timestamped quarantine key under CAS guards."""
    if not key.startswith(("network/ipam/", "network/session/")) or key.endswith("/meta"):
        raise NetworkStateQuarantineFailed(
            "only pool claims and session child records may be quarantined; session meta must be"
            " repaired at its source"
        )
    raw = await etcd.get(key, scope=ConfigScopes.GLOBAL)
    if raw is None:
        raise NetworkStateQuarantineFailed(f"{key} does not exist")
    ownership_guards = await _quarantine_guards(etcd, key, raw)
    quarantine_key = (
        f"network/quarantine/{int(time.time())}-{secrets.token_hex(4)}/{quote(key, safe='')}"
    )
    payload = json.dumps(
        {"original_key": key, "original_value": raw, "quarantined_at": time.time()},
        sort_keys=True,
    )
    if not await etcd.compare_and_put(
        quarantine_key,
        payload,
        expected=None,
        guards={key: raw, **ownership_guards},
    ):
        raise NetworkStateQuarantineFailed(f"{key} changed before it could be quarantined")
    if not await etcd.compare_and_delete(
        key,
        raw,
        guards={quarantine_key: payload, **ownership_guards},
    ):
        raise NetworkStateQuarantineFailed(
            f"{key} changed while it was copied; the snapshot remains at {quarantine_key}"
        )
    return quarantine_key
