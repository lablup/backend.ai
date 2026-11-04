# Agent RPC parity verification (`ag kernel`)

Purpose: verify that each agent re-architecture step (BEP-1057, Stories BA-6759…BA-6763)
leaves the agent's externally observable behavior unchanged, **without** golden snapshots.
The Docker kernel-create path needs a live daemon and is non-deterministic, so it is
unsuitable for `pants test -m 'not integration'`. Instead, drive the RPC of a running agent
directly and judge the result, either manually or with Claude.

`ag kernel` connects to the agent's RPC listen address over Callosum ZeroMQ and calls the
**same** RPC methods the manager uses, by reusing the shared `AgentClient`
(`ai.backend.common.clients.agent.client`). It is not a bypass path.

## Commands

| Command | RPC called | Observed |
|---------|-----------|----------|
| `ag kernel create --spec s.json` | `create_kernels` | returned kernel info (id, ports, container_id, resource_spec, …) |
| `ag kernel inspect --kernel-id …` | `check_creating` + `check_running` | `{creating, running}` |
| `ag kernel check-running --kernel-id …` | `check_running` | `{running}` |
| `ag kernel destroy --kernel-id … --session-id …` | `destroy_kernel` | teardown confirmation |
| `ag kernel pull --image …` | `check_and_pull` | per-image pull result |
| `ag kernel assign-port` | `assign_port` | assigned host port |
| `ag kernel local-network create/destroy --name …` | `create/destroy_local_network` | confirmation |

Connection information is read from the agent's own `agent.toml` (`-f/--config`). Pass
`--manager-keypair <manager.key_secret>` for RPC authentication.

## Spec (`KernelCreateSpec`)

The minimal spec is just `{"image": "<canonical>"}`. Every other field defaults to the launcher's
single-node value. The image must exist locally; run `ag kernel pull` first for a registry image.
`digest`, `labels` and `architecture` are auto-derived from `docker inspect`.

```json
{
  "image": "cr.backend.ai/stable/python:3.9-ubuntu20.04",
  "resource_slots": {"cpu": "1", "mem": "2147483648"},
  "environ": {},
  "scaling_group": "default"
}
```

## Per-step procedure

Run the cycle on the agent build **before** a refactor step and again **after**, then compare.

1. `ag kernel pull --image <img>` - ensure the image is present.
2. `ag kernel create --spec s.json` - capture `kernel_id`, `session_id` and `results` from stdout.
3. `ag kernel inspect --kernel-id <kid>` - expect `running: true` once startup completes.
4. Independently confirm the container: `docker ps --filter label=ai.backend.kernel-id=<kid>`.
5. `ag kernel destroy --kernel-id <kid> --session-id <sid>`.
6. `ag kernel inspect --kernel-id <kid>` - expect `creating: false, running: false`; the container is gone.

## Judgment criteria (manual / Claude)

Volatile fields are compared by **presence and structure**, not exact value. No golden
normalization is needed.

| Aspect | Compare by |
|--------|-----------|
| `container_id`, ports (`repl_*`, `stdin/stdout`, `service_ports`) | present and well-formed (non-empty, correct types); exact values differ every run |
| `resource_spec`, `attached_devices` | same shape and keys, and the requested slots reflected |
| `agent_addr`, `scaling_group` | equal to the configured values |
| kernel state | `create → running`, `destroy → not running`; same transition sequence |
| emitted events | same lifecycle sequence (`KernelPreparing/Pulling/Creating/Started` then `KernelTerminating/Terminated`) |

## Observing emitted events

`create_kernels` and `destroy_kernel` return synchronous payloads, captured above. Lifecycle
**events** flow to the event bus and do not return to this CLI. Observe them through the
`/observability` Grafana MCP (Loki): filter the agent's logs for `KernelStarted` and
`KernelTerminated` around the create and destroy timestamps, and confirm that the sequence
matches before and after the refactor. Pass `--emit-events` to `destroy` to keep the teardown
events, which the manager path suppresses.
