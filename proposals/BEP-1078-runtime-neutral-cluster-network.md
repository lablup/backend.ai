---
Author: Daemyung Jang (daemyung@lablup.com)
Status: Draft
Created: 2026-09-06
Created-Version: 26.9.0
Target-Version: 26.9.0
Implemented-Version:
---

# Runtime-Neutral Cluster Network

## Related Issues

- BEP-1057 (Agent Re-architecture)
- BEP-1061 (Agent Kernel Lifecycle Structuring)

## 1. Motivation

A multi-node cluster session needs one L2 domain across its kernels. Today that domain is a
Docker Swarm overlay network, which ties the feature to one container runtime: an agent running
containerd, enroot or apptainer has no way to join a session's network, and Swarm's IPAM and VNI
allocation are internal to a daemon the manager does not control.

This proposal moves the cluster network out of the runtime. The manager allocates the session's
address space and tunnel identity; each agent programs its own node's data plane through a CNI
plugin chain, driven by a backend that a runtime-neutral seam selects. The runtime's only role is
to hand over a container's network namespace.

## 2. Design

### 2.1 Layers

| Layer | Owner | Responsibility |
|-------|-------|----------------|
| Control plane | manager | subnet, VNI, per-endpoint IP, encryption key, membership |
| Agent plugin | agent | node data plane: devices, FDB/ARP, firewall, XFRM |
| Backend | agent | how the L2 domain is realized (`vxlan`, `bridge`) |
| Runtime seam | agent | netns of a container, by PID |

The seam names no runtime type: what a backend has to provide is a container's netns by PID, and
a netns does not care which daemon made it. `docker`, `enroot` and `singularity` ship provisioners
for it in this repository and `containerd` is named by the same enum; a backend that arrives
without the seam is refused on its published capabilities rather than by this list.

An agent joins a session by publishing a member record; it removes that record only once its
teardown has completed, which is what the manager reads before it reuses an allocation.

### 2.2 Control plane

Allocation state lives in etcd under `network/ipam/*` and `network/session/{id}/*`, claimed with
compare-and-swap.

| Key | Holds |
|-----|-------|
| `network/ipam/allocated/{block}` | the session that owns a unit block of the pool |
| `network/ipam/vni/{vni}` | the session that owns a VNI |
| `network/session/{id}/meta` | subnet, VNI, backend, MTU, VXLAN port, encryption key |
| `network/session/{id}/ipam/{ip}` | the container that holds an overlay address |
| `network/session/{id}/endpoints/{container}` | ip, mac, agent, cluster hostname |
| `network/session/{id}/members/{agent}` | an agent's VTEP, and its teardown acknowledgement |
| `network/agent/{id}/caps` | what the node's data plane can do |

`create_network` is idempotent on the session id: a retried session start converges on the
allocation already recorded rather than claiming a second one. An allocation is released only
once no member record remains.

Central IPAM — rather than host-local IPAM per node — is what guarantees disjoint addresses on a
subnet stretched across nodes, and the endpoints table is also the input each agent programs
FDB and ARP from.

### 2.3 Agent plugin

The plugin exposes the node's half of a session:

| Verb | Contract |
|------|----------|
| `setup_session_network` | make the node ready to carry the session |
| `attach` | put a container's netns on the session's L2 |
| `detach` | free the host veth, the host-local address, the MASQ rule |
| `add_peer` / `del_peer` | program one remote endpoint; both idempotent |
| `teardown_session_network` | leave nothing of this session on the node |

A node's privileged operations can be delegated to a separate `privnet` daemon, so the agent
itself needs no `CAP_NET_ADMIN`. That is opt-in: `network-privnet-socket` selects it, and with it
unset the agent does this work in-process and must hold the capabilities. Two agents sharing a
host share one privnet when it is used.

### 2.4 Cluster name resolution

Each session gets a resolver on the node that answers `cluster_hostname -> overlay ip` from the
endpoints table, so a kernel reaches its peers by name without a shared `/etc/hosts` write.

### 2.5 Encryption

The VXLAN backend encrypts the overlay by default, in ESP transport mode with
`rfc4106(gcm(aes))`, ESN and a replay window. The key is the cluster's, not the session's: ESP
policies select on the outer packet, which carries nothing identifying a session. The manager
turns encryption off for a session only when a member node's published capabilities say it
cannot do the profile, and refuses the session outright when policy is `required`.

## 3. Compatibility

The Swarm overlay plugin stays. `network.inter_container.default-driver` selects between them,
and an operator can pin a backend with `forced_backend`.
