<!-- context-for-ai
type: detail-doc
parent: BEP-1062 (Runtime-Neutral Cluster Network with Pluggable Data Plane)
scope: Encrypting the cross-node VXLAN overlay so a multi-node session's inter-kernel traffic is confidential on the wire, without moving packet crypto into userspace/Python.
depends-on: [control-plane.md, data-plane-backends.md]
key-decisions:
  - Crypto is KERNEL IPSec (ESP/AES-GCM + AES-NI), never Python. Python only programs XFRM — the same "Python configures, kernel forwards" split the VXLAN data plane already uses.
  - Encrypt the VXLAN tunnel with transport-mode ESP between VTEPs (Docker Swarm's model), keeping the L2 overlay unchanged.
  - One symmetric key for the CLUSTER, distributed via the session meta in etcd (like the VNI); no IKE, no per-pair negotiation. Deterministic SPI per ordered VTEP pair so both ends agree without a handshake.
  - XFRM state/policy is programmed per peer, right beside the FDB/ARP entry, by the coordinator→privnet path that already programs the fabric.
-->

# BEP-1062: Overlay Encryption

## Summary

A multi-node session's inter-kernel traffic rides a plaintext VXLAN overlay today — readable by anything that can see the underlay. This document adds **confidentiality on the wire** by encrypting the VXLAN tunnel with **kernel IPSec (ESP/AES-GCM)**, matching Docker Swarm's `--opt encrypted`. The crypto runs in the kernel (with AES-NI), so throughput stays at kernel/hardware speed; Python only programs the tunnel — the exact split the VXLAN data plane already uses (`ip link add type vxlan` + `bridge fdb`, kernel does encap/decap).

## Why not userspace / Python crypto

Encrypting every packet in userspace Python (interpreted, per-packet, context switches) would cap the fabric at a few Mbps — a non-starter for a data plane. **We never do that.** Overlay encryption is always kernel- or hardware-side:

| Layer | Where crypto runs | Python's job |
|---|---|---|
| **IPSec ESP** (chosen — Swarm's model) | kernel XFRM/ESP + AES-NI | `ip xfrm state/policy` (control plane only) |
| WireGuard | kernel `wg` module (ChaCha20) | `wg set` — but L3, changes our L2 model |

The privnet already runs `bridge fdb`/`ip neigh` to program the fabric; adding `ip xfrm` is the same kind of privileged control-plane call. **No packet ever touches Python.**

## Design

### Encrypt the VXLAN tunnel, keep the L2 overlay

Transport-mode ESP between the two nodes' **VTEP** addresses encrypts the VXLAN UDP (4789) carrying a session's frames. The VXLAN device, the FDB/ARP mesh, the LOCAL bridge — all unchanged; the overlay stays L2. This is Docker Swarm's exact approach and the reason we picked ESP over WireGuard (WireGuard is L3 and would replace or double-wrap the overlay).

### One cluster key, distributed like the VNI (no IKE)

The manager keeps one random 256-bit key for the cluster (created on first use, in etcd) and writes it into the **session meta** of every encrypted session (alongside `vni`/`subnet`/`mtu`). Every member node reads the same key — no IKE, no per-pair negotiation, no dedicated key-exchange component.

> **This started out as a key per session, and could not stay one.** ESP policies select on the
> OUTER packet — the two VTEP addresses and the VXLAN UDP port — and the VNI that identifies a
> session is inside that packet's payload, where no XFRM selector reaches. So every session between
> a pair of nodes shares one policy however many keys exist. Measured on this: with two SAs matching
> one policy, the kernel carried every packet on one and none on the other, and which one is not
> something either end chooses; and the first session to tear down deleted the shared policy, which
> dropped the sessions still running to clear text with nothing but a log line. A per-session key
> was a promise this layer cannot keep. Docker Swarm, which this design otherwise follows, uses a
> cluster key for the same reason. Session isolation on the overlay is the VNI's job (L2). This mirrors how the VNI is centrally allocated and read by all members (control-plane.md), and keeps the "reuse etcd, no new coordination" principle.

- `SessionNetMeta` gains `encryption_key: str | None` (hex; `None` = plaintext, the default).
- The key lives only in the control-plane etcd the agents already read; it is never sent to a kernel container.

### Deterministic SPI per ordered VTEP pair

Each ESP SA needs an SPI, and the two ends must agree on it without a handshake. Derive it deterministically from the ordered pair: `spi(a→b) = H(a, b)`. Node A's **out** SA to B and node B's **in** SA from A both compute `spi(A→B)` identically, so they match with no negotiation. Each direction is a distinct SA (`A→B` and `B→A` have different SPIs).

### Program XFRM beside the FDB — same path, same driver

Peer membership already flows coordinator → (privnet) → `bridge fdb`. Encryption rides the same path: when a peer's VTEP is programmed into the FDB (`add_peer`), the backend also installs, for that peer, the ESP **state** (both SAs) and **policy** (out/in) selecting the VXLAN UDP to/from that VTEP. On `del_peer`, both are withdrawn. So encryption is per-peer, keyed on the session, programmed by the CAP_NET_ADMIN holder (privnet, or the privileged agent) — never the unprivileged agent.

## Interface / API

- **etcd (read):** `SessionNetMeta.encryption_key` under the session meta. `None`/absent ⇒ plaintext (backward-compatible; existing sessions are untouched).
- **Agent backend:** the vxlan backend, given a keyed meta, installs XFRM state+policy per peer alongside the FDB entry (`ip xfrm state add … proto esp … aead 'rfc4106(gcm(aes))' <key>`; `ip xfrm policy add … dir out/in …` selecting `udp dport 4789` to/from the peer VTEP). Idempotent (`ip xfrm … update`/replace), withdrawn on `del_peer` and session teardown.
- **privnet RPC:** the existing peer-programming verbs carry the key (from the meta the privnet already receives at SETUP_SESSION), so the agent supplies no key material the privnet cannot already read — the privnet derives the SPI and installs XFRM itself.
- **Manager / config:** an `encrypted` session/scaling-group option; when set, the manager generates the key and writes it into the session meta at network setup.

## Implementation Notes

**Phasing:**

1. **Meta + key generation.** `SessionNetMeta.encryption_key`; the manager generates a 256-bit key when encryption is requested and writes it into the session meta. Backward-compatible (nullable).
2. **XFRM programming (agent/privnet).** The vxlan backend installs/withdraws ESP state+policy per peer beside the FDB, with the deterministic SPI. privnet gains the privileged `ip xfrm` execution (mirroring `bridge fdb`).
3. **Config surface.** The `encrypted` option (scaling-group/session), and the manager wiring that turns it into a keyed meta.
4. **Live validation.** 2-node encrypted session: cross-node inter-kernel traffic still flows; a capture on the underlay shows **ESP** (not cleartext VXLAN); `ip xfrm state` lists the SAs; toggling encryption off returns to plaintext.

**Costs / risks:**
- **MTU.** ESP adds overhead (~50–60 B) on top of VXLAN's 50. The overlay MTU handed to kernels must drop accordingly, or large frames fragment/blackhole (the same class of bug verified for VXLAN's MTU).
- **Key lifecycle.** One static key for the cluster (no rekey). Rotation is a non-goal for now; Swarm rotates roughly every 12 hours keeping three generations, which is the shape to copy when it is wanted.
- **AES-NI assumption.** Throughput assumes hardware AES (near line-rate); without it, AES-GCM in software is still far faster than any userspace option but not free.
- **SPI collision.** The deterministic SPI must be well-distributed over the 32-bit space. Concurrent sessions between the same two nodes are not a collision: they want the same SA, with the same key, and that is what they get — the agent refcounts the pair's state and policy by the sessions using them, so neither is programmed twice nor withdrawn while a session still needs it. A future rotation belongs in this hash, so two generations get distinct SPIs and can coexist while the change propagates.

**Non-goals:** IKE / dynamic key exchange; per-flow keys; rekeying; encrypting the LOCAL (node-internal) bridge (it never leaves the node); replacing the L2 overlay with WireGuard.
