# Data-plane tests — Guardrails

> Node-level tests for the containerd agent's network data plane (BEP-1062): netns, netlink
> devices, iptables, VXLAN FDB/ARP, containerd objects, and the durable state stores.
> These need a real host (root) and a live containerd — they are NOT unit tests.

Read `CONTEXTS.md` in this directory for why the suite is shaped this way.

## Scope

| Belongs here | Goes elsewhere |
|---|---|
| Host resource lifecycle (create → destroy → nothing left behind) | Pure logic on args/config → `tests/unit/agent/network/` |
| Restart / crash / adopt recovery across a real agent process | Manager-side API flows → `tests/integration/` |
| Cross-node overlay reachability, isolation, MTU | HTTP routing/auth → `tests/component/` |
| Concurrency and churn against real allocators | |

## Opt-in only

Every fixture that touches a host is gated on `BAI_DATAPLANE_NODES`. With it unset the suite
still runs — but only `test_harness_selfcheck.py`, which exercises the harness against fake
nodes and needs no privileges. `pants test ::` must stay safe on a developer laptop.

## The leak guard is the point

Attach `leak_guard` to **every** test that creates a session. A data-plane test that only asserts
"it worked" is worth little: every defect this backend has shipped so far was a resource that
survived teardown. See `guard.py`.

- Assert on the **delta** against a baseline, never on absolute zero — the host may legitimately
  carry devices from other agents or pre-existing sessions.
- A collector that cannot run MUST raise, never return an empty set. A silent empty snapshot
  reads as "no leaks" and is the one failure mode that makes the whole suite lie.

## Adding a collector

1. Subclass `ResourceCollector` in `collectors/`, return `Resource(kind, node, ident, detail)`.
2. `detail` is excluded from identity — put volatile text (status, counters) there, never in `ident`.
3. Add a self-check to `test_harness_selfcheck.py` with captured real output as the fixture text.
4. Register it in `conftest.py::_build_collectors`.

## BUILD files

`python_test_utils(sources=["*.py", "!test_*.py"])` + `python_tests(name="tests")` per directory.
