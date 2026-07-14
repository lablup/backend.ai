"""
``ag kernel`` — drive a running agent's kernel RPC directly for parity checks.

This command group connects over Callosum ZeroMQ to a running agent's RPC listen
address and invokes the **same** RPC methods the manager uses, by reusing the
shared ``AgentClient`` (``ai.backend.common.clients.agent.client``). It is the
parity-verification tool for the agent re-architecture (BEP-1057): run
``create -> inspect -> destroy`` before and after each refactor step and confirm
the observed container / returned kernel info / state transitions are unchanged.

Connection uses the agent's own ``agent.toml`` (``-f/--config``): the RPC listen
address and auth keypair are read from it. When the agent runs without RPC auth
(the local-dev default, ``rpc-auth-agent-keypair`` unset) no keypair is needed.
When auth is enabled, pass ``--manager-keypair`` pointing at the manager's
``*.key_secret`` file.

See ``PARITY.md`` in this directory for the per-step verification procedure.
"""

from __future__ import annotations

import asyncio
import functools
import json
import uuid
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import click

from .context import CLIContext

if TYPE_CHECKING:
    from ai.backend.agent.config.unified import AgentUnifiedConfig
    from ai.backend.common.clients.agent.client import AgentClient
    from ai.backend.common.types import ImageConfig

    from .kernel_spec import KernelCreateSpec


# --- connection wiring -------------------------------------------------------


def _load_agent_config(config_path: Path | None) -> AgentUnifiedConfig:
    """Load ``AgentUnifiedConfig`` from the agent's toml (same path the agent uses)."""
    from ai.backend.agent.config.unified import (
        AgentConfigValidationContext,
        AgentUnifiedConfig,
    )
    from ai.backend.common import config as common_config
    from ai.backend.logging.types import LogLevel

    raw_cfg, _ = common_config.read_from_file(config_path, "agent")
    common_config.override_with_env(
        raw_cfg, ("agent", "rpc-listen-addr", "host"), "BACKEND_AGENT_HOST_OVERRIDE"
    )
    common_config.override_with_env(
        raw_cfg, ("agent", "rpc-listen-addr", "port"), "BACKEND_AGENT_PORT"
    )
    return AgentUnifiedConfig.model_validate(
        raw_cfg,
        context=AgentConfigValidationContext(
            debug=False,
            log_level=LogLevel.NOTSET,
            is_invoked_subcommand=True,
        ),
    )


def _resolve_agent_addr(cfg: AgentUnifiedConfig) -> str:
    """Build the ``tcp://host:port`` the CLI should dial for the local agent."""
    rpc_addr = cfg.agent_common.rpc_listen_addr
    host = rpc_addr.host
    if host in ("0.0.0.0", "::", ""):
        # The agent binds a wildcard host; dial loopback to reach it locally.
        host = "127.0.0.1"
    return f"tcp://{host}:{rpc_addr.port}"


def _build_auth_handler(
    cfg: AgentUnifiedConfig,
    manager_keypair: Path | None,
) -> Any | None:
    """Build a ``ManagerAuthHandler`` when the agent has RPC auth enabled, else None."""
    agent_keypair = cfg.agent_common.rpc_auth_agent_keypair
    if agent_keypair is None:
        # Agent binds RPC without CURVE auth (local-dev default).
        return None
    if manager_keypair is None:
        raise click.ClickException(
            "The agent has RPC auth enabled (rpc-auth-agent-keypair is set); "
            "pass --manager-keypair pointing at the manager's *.key_secret file."
        )
    from zmq.auth.certs import load_certificate

    from ai.backend.common.auth import ManagerAuthHandler, PublicKey, SecretKey

    agent_public_key, _ = load_certificate(str(agent_keypair))
    manager_public_key, manager_secret_key = load_certificate(str(manager_keypair))
    if manager_secret_key is None:
        raise click.ClickException(
            f"Manager keypair '{manager_keypair}' has no secret key; "
            "point --manager-keypair at the *.key_secret file."
        )
    return ManagerAuthHandler(
        "local",
        PublicKey(agent_public_key),
        PublicKey(manager_public_key),
        SecretKey(manager_secret_key),
    )


@asynccontextmanager
async def _connect_agent(
    config_path: Path | None,
    agent_id: str | None,
    manager_keypair: Path | None,
) -> AsyncIterator[AgentClient]:
    """Open a single ``AgentClient`` to the local running agent.

    Mirrors ``AgentClientPool._create_peer`` for the peer construction, but
    resolves the address/auth from the agent's config file instead of the
    manager DB. The RPC calls themselves go through the shared ``AgentClient``,
    so this is the manager's exact RPC path, not a bypass.
    """
    import zmq
    from callosum.lower.zeromq import ZeroMQAddress, ZeroMQRPCTransport

    from ai.backend.common import msgpack
    from ai.backend.common.clients.agent.client import AgentClient
    from ai.backend.common.clients.agent.peer import PeerInvoker
    from ai.backend.common.types import AgentId

    cfg = _load_agent_config(config_path)
    agent_addr = _resolve_agent_addr(cfg)
    auth_handler = _build_auth_handler(cfg, manager_keypair)
    # None agent_id targets the agent's primary agent server-side (get_agent(None)).
    resolved_agent_id = agent_id or cfg.agent_default.id

    peer = PeerInvoker(
        connect=ZeroMQAddress(agent_addr),
        transport=ZeroMQRPCTransport,
        authenticator=auth_handler,
        transport_opts={
            "zsock_opts": {
                zmq.TCP_KEEPALIVE: 1,
                zmq.TCP_KEEPALIVE_IDLE: 60,
                zmq.TCP_KEEPALIVE_INTVL: 20,
                zmq.TCP_KEEPALIVE_CNT: 3,
            },
        },
        serializer=msgpack.packb,
        deserializer=msgpack.unpackb,
    )
    client = AgentClient(peer, cast(AgentId, resolved_agent_id))
    click.echo(f"# connecting to agent RPC at {agent_addr}", err=True)
    await client.connect()
    try:
        yield client
    finally:
        await client.close()


def _connection_options(func: Callable[..., Any]) -> Callable[..., Any]:
    """Shared ``--agent-id`` / ``--manager-keypair`` options for connecting commands."""

    @click.option(
        "--agent-id",
        default=None,
        help="Target agent id. Defaults to the config's agent id, or the primary agent.",
    )
    @click.option(
        "--manager-keypair",
        type=click.Path(exists=True, dir_okay=False, path_type=Path),
        default=None,
        help="Manager *.key_secret file (only when the agent has RPC auth enabled).",
    )
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    return wrapper


# --- image resolution --------------------------------------------------------


async def _inspect_local_image(canonical: str) -> dict[str, Any] | None:
    """Inspect a local docker image; return None when it is not present."""
    from aiodocker.docker import Docker
    from aiodocker.exceptions import DockerError
    from aiotools import closing_async

    async with closing_async(Docker()) as docker:
        try:
            return await docker.images.inspect(canonical)
        except DockerError as e:
            if e.status == 404:
                return None
            raise


def _image_config_from_inspect(
    spec: KernelCreateSpec,
    inspect: dict[str, Any],
) -> ImageConfig:
    """Fill an ``ImageConfig`` from a local ``docker inspect`` result.

    ``digest`` maps to the image ``Id`` (what the agent's ``check_image``
    compares under ``auto_pull=digest``); ``architecture`` is aliased to the
    Backend.AI arch name and must match the host arch.
    """
    from ai.backend.common.docker import arch_name_aliases
    from ai.backend.common.types import ImageConfig

    raw_arch = inspect.get("Architecture", "x86_64")
    architecture = spec.architecture or arch_name_aliases.get(raw_arch, raw_arch)
    labels = (inspect.get("Config") or {}).get("Labels") or {}
    repo_digests = inspect.get("RepoDigests") or []
    repo_digest = repo_digests[0].partition("@")[-1] if repo_digests else None
    return ImageConfig(
        canonical=spec.image,
        project=spec.project,
        architecture=architecture,
        digest=inspect["Id"],
        repo_digest=repo_digest,
        registry={
            "name": spec.registry.name,
            "url": spec.registry.url,
            "username": spec.registry.username,
            "password": spec.registry.password,
        },
        labels=labels,
        is_local=spec.is_local,
        auto_pull=spec.auto_pull,
    )


def _image_config_from_spec(spec: KernelCreateSpec, digest: str) -> ImageConfig:
    """Build an ``ImageConfig`` purely from the spec (image not present locally)."""
    from ai.backend.common.types import ImageConfig

    return ImageConfig(
        canonical=spec.image,
        project=spec.project,
        architecture=spec.architecture or "x86_64",
        digest=digest,
        repo_digest=None,
        registry={
            "name": spec.registry.name,
            "url": spec.registry.url,
            "username": spec.registry.username,
            "password": spec.registry.password,
        },
        labels={},
        is_local=spec.is_local,
        auto_pull=spec.auto_pull,
    )


def _load_spec(spec_path: Path | None, image: str | None) -> KernelCreateSpec:
    """Load a ``KernelCreateSpec`` from a JSON file and/or a plain image override."""
    from .kernel_spec import KernelCreateSpec

    data: dict[str, Any] = {}
    if spec_path is not None:
        data = json.loads(spec_path.read_text())
    if image is not None:
        data["image"] = image
    if "image" not in data:
        raise click.ClickException(
            "No image given: provide --spec with an 'image' field or --image."
        )
    return KernelCreateSpec.model_validate(data)


def _jsonable(obj: Any) -> Any:
    """Coerce an RPC result into a JSON-serialisable structure.

    Agent RPC payloads contain non-``str`` mapping keys (e.g. ``SlotName`` in
    ``resource_spec``) and typed scalars that ``json.dumps`` rejects even with
    ``default=str`` (which only covers values, not keys). Walk the structure and
    stringify keys / unknown scalars so the CLI can always print the result.
    """
    from collections.abc import Mapping, Sequence

    if isinstance(obj, Mapping):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (str, bytes)):
        return obj.decode() if isinstance(obj, bytes) else obj
    if isinstance(obj, Sequence):
        return [_jsonable(v) for v in obj]
    if obj is None or isinstance(obj, (bool, int, float)):
        return obj
    return str(obj)


def _echo_json(payload: Any) -> None:
    click.echo(json.dumps(_jsonable(payload), indent=2, sort_keys=True))


# --- command group -----------------------------------------------------------


@click.group()
def cli() -> None:
    """Drive a running agent's kernel RPC (parity verification / ops-debug)."""


@cli.command()
@click.option(
    "--spec",
    "spec_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="JSON file describing the kernel to create (see KernelCreateSpec).",
)
@click.option("--image", default=None, help="Image canonical string (overrides spec.image).")
@click.option("--kernel-id", default=None, help="Override the generated kernel id (UUID).")
@click.option("--session-id", default=None, help="Override the generated session id (UUID).")
@_connection_options
@click.pass_obj
def create(
    cli_ctx: CLIContext,
    spec_path: Path | None,
    image: str | None,
    kernel_id: str | None,
    session_id: str | None,
    agent_id: str | None,
    manager_keypair: Path | None,
) -> None:
    """Create a kernel from a spec on the running agent and print the kernel info.

    The image must exist locally (built or pulled); use ``ag kernel pull`` first
    for a registry image. Generated kernel/session/owner ids are printed so a
    follow-up ``inspect`` / ``destroy`` can target the same kernel.
    """
    from .kernel_spec import (
        build_cluster_info,
        build_image_ref,
        build_kernel_creation_config,
        generate_cluster_ssh_keypair,
    )

    spec = _load_spec(spec_path, image)
    kernel_id = kernel_id or str(uuid.uuid4())
    session_id = session_id or str(uuid.uuid4())
    owner_user_id = spec.owner_user_id or str(uuid.uuid4())

    async def _run() -> None:
        from ai.backend.common.types import KernelId, SessionId

        inspect = await _inspect_local_image(spec.image)
        if inspect is None:
            raise click.ClickException(
                f"Image '{spec.image}' is not present locally. "
                "Run 'ag kernel pull' first, or build/tag it."
            )
        image_config = _image_config_from_inspect(spec, inspect)

        async with _connect_agent(cli_ctx.config_path, agent_id, manager_keypair) as client:
            agent_addr = _resolve_agent_addr(_load_agent_config(cli_ctx.config_path))
            kernel_config = build_kernel_creation_config(
                spec,
                image_config=image_config,
                kernel_id=kernel_id,
                session_id=session_id,
                owner_user_id=owner_user_id,
                agent_addr=agent_addr,
            )
            cluster_info = build_cluster_info(spec, generate_cluster_ssh_keypair())
            image_ref = build_image_ref(image_config)
            kid = KernelId(uuid.UUID(kernel_id))
            results = await client.create_kernels(
                SessionId(uuid.UUID(session_id)),
                [kid],
                [kernel_config],
                cluster_info,
                {kid: image_ref},
            )
        _echo_json({
            "kernel_id": kernel_id,
            "session_id": session_id,
            "owner_user_id": owner_user_id,
            "results": results,
        })

    asyncio.run(_run())


@cli.command()
@click.option("--kernel-id", required=True, help="Kernel id (UUID) to destroy.")
@click.option("--session-id", required=True, help="Session id (UUID) of the kernel.")
@click.option("--reason", default="user-requested", help="Termination reason.")
@click.option(
    "--suppress-events/--emit-events",
    default=False,
    help="Whether the agent suppresses lifecycle events for this teardown.",
)
@_connection_options
@click.pass_obj
def destroy(
    cli_ctx: CLIContext,
    kernel_id: str,
    session_id: str,
    reason: str,
    suppress_events: bool,
    agent_id: str | None,
    manager_keypair: Path | None,
) -> None:
    """Destroy a kernel on the running agent and print the teardown result."""

    async def _run() -> None:
        from ai.backend.common.types import KernelId, SessionId

        async with _connect_agent(cli_ctx.config_path, agent_id, manager_keypair) as client:
            # AgentClient.destroy_kernel discards the agent's return payload
            # (matching the manager's contract), so observe teardown via a
            # follow-up `inspect` / `check-running` and the emitted events.
            await client.destroy_kernel(
                KernelId(uuid.UUID(kernel_id)),
                SessionId(uuid.UUID(session_id)),
                reason,
                suppress_events=suppress_events,
            )
        _echo_json({"kernel_id": kernel_id, "destroyed": True})

    asyncio.run(_run())


@cli.command(name="check-running")
@click.option("--kernel-id", required=True, help="Kernel id (UUID) to check.")
@_connection_options
@click.pass_obj
def check_running(
    cli_ctx: CLIContext,
    kernel_id: str,
    agent_id: str | None,
    manager_keypair: Path | None,
) -> None:
    """Report whether a kernel is in the RUNNING state on the agent."""

    async def _run() -> None:
        from ai.backend.common.types import KernelId

        async with _connect_agent(cli_ctx.config_path, agent_id, manager_keypair) as client:
            running = await client.check_running(KernelId(uuid.UUID(kernel_id)))
        _echo_json({"kernel_id": kernel_id, "running": running})

    asyncio.run(_run())


@cli.command()
@click.option("--kernel-id", required=True, help="Kernel id (UUID) to inspect.")
@_connection_options
@click.pass_obj
def inspect(
    cli_ctx: CLIContext,
    kernel_id: str,
    agent_id: str | None,
    manager_keypair: Path | None,
) -> None:
    """Report a kernel's creating/running state via the agent RPC."""

    async def _run() -> None:
        from ai.backend.common.types import KernelId

        kid = KernelId(uuid.UUID(kernel_id))
        async with _connect_agent(cli_ctx.config_path, agent_id, manager_keypair) as client:
            creating = await client.check_creating(kid)
            running = await client.check_running(kid)
        _echo_json({"kernel_id": kernel_id, "creating": creating, "running": running})

    asyncio.run(_run())


@cli.command()
@click.option(
    "--spec",
    "spec_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="JSON spec (uses its image/registry/architecture fields).",
)
@click.option("--image", default=None, help="Image canonical string (overrides spec.image).")
@click.option("--digest", default="", help="Expected image Id (sha256:...) for digest auto-pull.")
@_connection_options
@click.pass_obj
def pull(
    cli_ctx: CLIContext,
    spec_path: Path | None,
    image: str | None,
    digest: str,
    agent_id: str | None,
    manager_keypair: Path | None,
) -> None:
    """Check-and-pull an image on the agent (mirrors the manager's pull step)."""
    spec = _load_spec(spec_path, image)

    async def _run() -> None:
        inspect = await _inspect_local_image(spec.image)
        if inspect is not None:
            image_config = _image_config_from_inspect(spec, inspect)
        else:
            image_config = _image_config_from_spec(spec, digest)
        async with _connect_agent(cli_ctx.config_path, agent_id, manager_keypair) as client:
            result = await client.check_and_pull({spec.image: image_config})
        _echo_json({"image": spec.image, "result": result})

    asyncio.run(_run())


@cli.command(name="assign-port")
@_connection_options
@click.pass_obj
def assign_port(
    cli_ctx: CLIContext,
    agent_id: str | None,
    manager_keypair: Path | None,
) -> None:
    """Assign a free host port on the agent (helper RPC)."""

    async def _run() -> None:
        async with _connect_agent(cli_ctx.config_path, agent_id, manager_keypair) as client:
            port = await client.assign_port()
        _echo_json({"port": port})

    asyncio.run(_run())


@cli.group(name="local-network")
def local_network() -> None:
    """Manage agent-local docker networks (helper RPC)."""


@local_network.command(name="create")
@click.option("--name", required=True, help="Local network name to create.")
@_connection_options
@click.pass_obj
def local_network_create(
    cli_ctx: CLIContext,
    name: str,
    agent_id: str | None,
    manager_keypair: Path | None,
) -> None:
    """Create a local network on the agent."""

    async def _run() -> None:
        async with _connect_agent(cli_ctx.config_path, agent_id, manager_keypair) as client:
            await client.create_local_network(name)
        _echo_json({"created": name})

    asyncio.run(_run())


@local_network.command(name="destroy")
@click.option("--name", required=True, help="Local network name (ref) to destroy.")
@_connection_options
@click.pass_obj
def local_network_destroy(
    cli_ctx: CLIContext,
    name: str,
    agent_id: str | None,
    manager_keypair: Path | None,
) -> None:
    """Destroy a local network on the agent."""

    async def _run() -> None:
        async with _connect_agent(cli_ctx.config_path, agent_id, manager_keypair) as client:
            await client.destroy_local_network(name)
        _echo_json({"destroyed": name})

    asyncio.run(_run())
