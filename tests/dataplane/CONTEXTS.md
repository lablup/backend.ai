# Data-plane tests — Context

Background for the guardrails in `AGENTS.md`. Read this before changing the harness.

## Why this suite exists

`tests/unit/agent/network/` covers the pure logic well — argument construction, config assembly,
allocator arithmetic. What it cannot cover is the thing that has actually broken: the host's kernel
state after a real session has come and gone. Every defect the containerd/VXLAN work has shipped so
far was a resource that survived teardown or a record that outlived its owner — a leaked subnet
block, a stale VTEP key, a container the agent forgot, an fd nobody closed. None of those are
visible to a mocked test, and all of them are visible to a diff of the host.

`tests/integration/` cannot cover them either: it drives the manager's API through the Client SDK
and is deliberately blind to what an agent did to its own host.

## Why a delta, not an absolute

The obvious design — "after teardown, no `bai*` device exists" — fails on any host that runs more
than one agent, co-hosts Docker, or has a session from a previous run. It would be disabled within
a week. Baselining before the scenario and diffing after keeps the assertion true on a shared
developer host, and it is what makes the guard safe to attach to *every* test by default.

The cost is that a resource leaked by an *earlier* test lands in the next test's baseline and stops
being reported. That is the right trade: the first test to leak it still fails.

## Why the guard polls

Teardown is asynchronous through every layer — the API returns before the agent has finished, the
agent returns before containerd has reaped the shim, containerd returns before the runner has torn
down the bridge. A single sample taken right after teardown is flaky in the worst direction: it
fails intermittently, someone adds a `sleep`, and the sleep hides a genuine slowdown later.

Polling to a deadline removes the flake and turns settle time into data. `LeakReport.elapsed` is
worth watching: teardown that grew from 2s to 20s is a regression the pass/fail bit cannot show.

## Why collectors must fail loudly

This is the only design rule in the suite that is not negotiable. A collector that returns an empty
set when it cannot run reports a leaking host as clean, and no one would notice — the suite would
be green while covering nothing. So `iptables-save` failing on a missing sudoers entry, `ip`
returning something that is not JSON, and `ctr` failing to reach the socket all raise.

The self-check suite (`test_harness_selfcheck.py`) exists for the same reason, and runs with no
privileges so it cannot be skipped by accident.

## Things the host taught us

Both of these were found by running the harness against a live host, after it had already passed
its own tests — the reason the harness is validated against real captured output rather than
hand-written fixtures.

| Finding | Consequence |
|---|---|
| `ip -details -json link show` emits invalid JSON when a VXLAN device is present (iproute2 6.1.0 prints the fan-map as raw text inside the object) | The link collector must not pass `-details`. Production code does not parse `ip -json`, so it is unaffected. |
| `pgrep -f <pattern>` matches the `sh -c`/`sudo` running it | Gauge rows naming `pgrep` are dropped in `parse`; without that, the gauge set churns every poll and real drift hides in the noise. |

## What is deliberately not collected

- **Images and content blobs.** The image cache is meant to be durable across sessions. A scenario
  that asserts on commits should warm the cache *before* `baseline()`.
- **Long-lived agent advertisements** (`network/agent/{id}/caps|backend|vtep`) are collected, but
  they sit in the baseline while the agent runs, so they only surface when a scenario changes them
  — which is exactly when they matter.
