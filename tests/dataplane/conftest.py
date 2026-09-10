"""Fixtures for the data-plane suite.

The whole suite is opt-in through ``BAI_DATAPLANE_NODES``. With it unset, every host-touching
fixture skips and only the harness self-check runs — `pants test ::` on a laptop must not start
poking at iptables.
"""

from __future__ import annotations

import asyncio
import os
import shlex
from collections.abc import AsyncIterator, Awaitable, Callable, Generator, Sequence
from dataclasses import dataclass, field
from uuid import UUID

import pytest
import yarl

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.types import HostPortPair
from ai.backend.testutils.dataplane.agent_control import AgentControlConfig, AgentController
from ai.backend.testutils.dataplane.collectors.base import ResourceCollector
from ai.backend.testutils.dataplane.collectors.containerd_objects import ContainerdObjectCollector
from ai.backend.testutils.dataplane.collectors.docker_objects import (
    DockerKernelContainerCollector,
    docker_collectors,
)
from ai.backend.testutils.dataplane.collectors.etcd_keys import EtcdNetworkKeyCollector
from ai.backend.testutils.dataplane.collectors.gauges import ProcessGaugeCollector
from ai.backend.testutils.dataplane.collectors.host import (
    IptablesRuleCollector,
    MountCollector,
    NeighbourCollector,
    NetworkLinkCollector,
    ScratchDirCollector,
    StateFileCollector,
    XfrmCollector,
)
from ai.backend.testutils.dataplane.guard import LeakGuard
from ai.backend.testutils.dataplane.nodes import Node, SudoNode, parse_node_specs
from ai.backend.testutils.dataplane.session import SessionDriver, SessionSpec

ENV_NODES = "BAI_DATAPLANE_NODES"
ENV_AGENT_IDS = "BAI_DATAPLANE_AGENT_IDS"
ENV_RELEASE_GATE = "BAI_REQUIRE_DATAPLANE"
RELEASE_GATE_REQUIRED_ENV = (
    ENV_NODES,
    "BAI_DATAPLANE_ACCESS_KEY",
    ENV_AGENT_IDS,
    "BAI_DATAPLANE_AGENT_START_CMD",
    "BAI_DATAPLANE_ETCD_ADDR",
    "BAI_DATAPLANE_IMAGE_ID",
    "BAI_DATAPLANE_MANAGER",
    "BAI_DATAPLANE_PRIVNET_MODE",
    "BAI_DATAPLANE_PRIVNET_SOCKET",
    "BAI_DATAPLANE_PROJECT_ID",
    "BAI_DATAPLANE_SECRET_KEY",
)


@dataclass(frozen=True)
class DataplaneConfig:
    runtime: str = "docker"
    state_root: str = "/var/lib/backend.ai"
    scratch_roots: tuple[str, ...] = ("/var/lib/backend.ai/scratches",)
    containerd_address: str = "/run/containerd/containerd.sock"
    containerd_namespace: str = "backend-ai"
    etcd_addr: HostPortPair = field(
        default_factory=lambda: HostPortPair(host="127.0.0.1", port=8120)
    )
    etcd_namespace: str = "local"
    agent_process_pattern: str = "ai.backend.agent"
    use_sudo: bool = True
    manager_endpoint: str = "http://127.0.0.1:8091"
    access_key: str = ""
    secret_key: str = ""
    image_id: str = ""
    project_id: str = ""
    agent_start_cmd: tuple[str, ...] = ()
    agent_stop_cmd: tuple[str, ...] = ()
    agent_rpc_port: int = 6011
    privnet_mode: bool = False
    """Whether the agent delegates host networking to a privnet daemon. Single-node cluster peer
    resolution is unimplemented in that mode (the privnet owns the LOCAL pool the addresses are
    computed from), so a scenario that needs it xfails rather than reporting a bug already known."""
    agent_ids: tuple[str, ...] = ()
    """The manager's agent id for each node, in the same order as ``BAI_DATAPLANE_NODES``. A
    scenario pins a session to one of these so it lands on the node it inspects: with a second
    agent registered in the group the scheduler is free to place a single-node session on either,
    and a co-location scenario that read the wrong node would find no kernel."""
    privnet_socket: str = "/run/backend.ai/privnet/net-privnet.sock"

    @property
    def state_dirs(self) -> tuple[str, ...]:
        return (
            f"{self.state_root}/net-local-subnet",
            f"{self.state_root}/net-ipam",
        )


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


def _release_gate_required() -> bool:
    return _env(ENV_RELEASE_GATE, "0") == "1"


def _unavailable(reason: str) -> None:
    if _release_gate_required():
        pytest.fail(f"data-plane release gate prerequisite failed: {reason}", pytrace=False)
    pytest.skip(reason)


@pytest.fixture(scope="session", autouse=True)
def release_gate_preflight() -> None:
    """Fail before touching hosts when a production gate is incomplete."""
    if not _release_gate_required():
        return
    missing = [name for name in RELEASE_GATE_REQUIRED_ENV if not _env(name, "").strip()]
    if missing:
        pytest.fail(
            "data-plane release gate is missing: " + ", ".join(missing),
            pytrace=False,
        )
    node_specs = [value.strip() for value in _env(ENV_NODES, "").split(",") if value.strip()]
    node_targets = [
        value.partition("=")[2] if "=" in value and not value.startswith("ssh://") else value
        for value in node_specs
    ]
    agent_ids = [
        value.strip() for value in _env("BAI_DATAPLANE_AGENT_IDS", "").split(",") if value.strip()
    ]
    if len(node_specs) < 2 or len(set(node_targets)) != len(node_targets):
        pytest.fail(
            "data-plane release gate requires at least two distinct node specifications",
            pytrace=False,
        )
    if len(agent_ids) != len(node_specs) or len(set(agent_ids)) != len(agent_ids):
        pytest.fail(
            "BAI_DATAPLANE_AGENT_IDS must name one distinct agent per node",
            pytrace=False,
        )
    runtime = _env("BAI_DATAPLANE_RUNTIME", "docker")
    if runtime != "docker":
        pytest.fail(
            "the production gate requires BAI_DATAPLANE_RUNTIME=docker; other runtime seams are "
            "not implemented",
            pytrace=False,
        )
    if _env("BAI_DATAPLANE_PRIVNET_MODE", "0") != "1":
        pytest.fail(
            "the production gate requires BAI_DATAPLANE_PRIVNET_MODE=1",
            pytrace=False,
        )


@pytest.fixture(scope="session")
def dataplane_config() -> DataplaneConfig:
    host, _, port = _env("BAI_DATAPLANE_ETCD_ADDR", "127.0.0.1:8120").rpartition(":")
    return DataplaneConfig(
        runtime=_env("BAI_DATAPLANE_RUNTIME", "docker"),
        state_root=_env("BAI_DATAPLANE_STATE_ROOT", "/var/lib/backend.ai"),
        scratch_roots=tuple(
            p
            for p in _env("BAI_DATAPLANE_SCRATCH_ROOTS", "/var/lib/backend.ai/scratches").split(",")
            if p
        ),
        containerd_address=_env(
            "BAI_DATAPLANE_CONTAINERD_ADDRESS", "/run/containerd/containerd.sock"
        ),
        containerd_namespace=_env("BAI_DATAPLANE_CONTAINERD_NAMESPACE", "backend-ai"),
        etcd_addr=HostPortPair(host=host or "127.0.0.1", port=int(port)),
        etcd_namespace=_env("BAI_DATAPLANE_ETCD_NAMESPACE", "local"),
        agent_process_pattern=_env("BAI_DATAPLANE_AGENT_PATTERN", "ai.backend.agent"),
        use_sudo=_env("BAI_DATAPLANE_SUDO", "1") != "0",
        manager_endpoint=_env("BAI_DATAPLANE_MANAGER", "http://127.0.0.1:8091"),
        access_key=_env("BAI_DATAPLANE_ACCESS_KEY", ""),
        secret_key=_env("BAI_DATAPLANE_SECRET_KEY", ""),
        image_id=_env("BAI_DATAPLANE_IMAGE_ID", ""),
        project_id=_env("BAI_DATAPLANE_PROJECT_ID", ""),
        agent_start_cmd=tuple(shlex.split(_env("BAI_DATAPLANE_AGENT_START_CMD", ""))),
        agent_stop_cmd=tuple(shlex.split(_env("BAI_DATAPLANE_AGENT_STOP_CMD", ""))),
        agent_rpc_port=int(_env("BAI_DATAPLANE_AGENT_RPC_PORT", "6011")),
        privnet_mode=_env("BAI_DATAPLANE_PRIVNET_MODE", "0") != "0",
        privnet_socket=_env(
            "BAI_DATAPLANE_PRIVNET_SOCKET", "/run/backend.ai/privnet/net-privnet.sock"
        ),
        agent_ids=tuple(p for p in _env("BAI_DATAPLANE_AGENT_IDS", "").split(",") if p),
    )


@pytest.fixture(scope="session", autouse=True)
def release_gate_privnet_preflight(
    request: pytest.FixtureRequest, dataplane_config: DataplaneConfig
) -> None:
    """Require a reachable privnet socket from the agent account on every release-gate node."""
    if not _release_gate_required():
        return
    raw_nodes: Sequence[Node] = request.getfixturevalue("raw_nodes")
    probe = (
        "import socket,sys; "
        "s=socket.socket(socket.AF_UNIX); s.settimeout(2); s.connect(sys.argv[1]); s.close()"
    )

    async def check_nodes() -> None:
        for node in raw_nodes:
            result = await node.run(
                ["python3", "-c", probe, dataplane_config.privnet_socket], check=False
            )
            if result.returncode != 0:
                pytest.fail(
                    f"[{node.name}] privnet socket is not reachable at "
                    f"{dataplane_config.privnet_socket}: {result.stderr.strip()}",
                    pytrace=False,
                )

    asyncio.run(check_nodes())


@pytest.fixture(scope="session")
def raw_nodes(dataplane_config: DataplaneConfig) -> Sequence[Node]:
    """The nodes without the sudo wrapper.

    Collectors need root (iptables, the containerd socket, other users' /proc), so `nodes` wraps
    these. But the agent runs as the developer, and its lifecycle commands must NOT be sudo'd:
    starting it under sudo runs the agent as root, and a root agent is refused by the privnet,
    which only trusts the developer's uid -- a mismatch that hangs every session at network setup.
    """
    raw = os.environ.get(ENV_NODES, "").strip()
    if not raw:
        _unavailable(f"{ENV_NODES} is unset; data-plane tests need a host to run against")
    return parse_node_specs(raw)


@pytest.fixture(scope="session")
def nodes(raw_nodes: Sequence[Node], dataplane_config: DataplaneConfig) -> Sequence[Node]:
    if dataplane_config.use_sudo:
        return [SudoNode(node) for node in raw_nodes]
    return list(raw_nodes)


@pytest.fixture(scope="session")
def node(nodes: Sequence[Node]) -> Node:
    return nodes[0]


@pytest.fixture
def agent_ids(dataplane_config: DataplaneConfig) -> tuple[str, ...]:
    """The manager's agent id per node, for scenarios that pin a session's placement.

    Skips when unset: a co-location or cross-node scenario cannot control where the scheduler puts
    a session without it, so it declines rather than silently testing the wrong node.
    """
    if not dataplane_config.agent_ids:
        _unavailable("BAI_DATAPLANE_AGENT_IDS is unset; placement-pinned scenarios need it")
    return dataplane_config.agent_ids


@pytest.fixture
def pair_agent_ids(agent_ids: tuple[str, ...]) -> tuple[str, ...]:
    """The agent ids of `node_pair`, for a scenario that then inspects only those two nodes.

    `BAI_DATAPLANE_AGENT_IDS` is per node in the same order as `BAI_DATAPLANE_NODES`, so the pair
    is the first two. Cross-node scenarios pinned to the WHOLE list instead, which is placement on
    two nodes only while the rig has exactly two: add a third and the scheduler may put both
    kernels on it, or on one node big enough for both, and the scenario reports the pair it looked
    at as unspread and skips. Measured on a three-node rig: one run skipped the cross-node
    reachability check, the next skipped the MTU one, and the IPAM check -- which asserts where the
    others skip -- failed with one endpoint instead of two.

    Asking for the spread by CPU shape cannot replace this: a node larger than the rest fits both
    kernels whatever each one asks for.
    """
    if len(agent_ids) < 2:
        _unavailable(f"needs two agent ids; {ENV_AGENT_IDS} names {len(agent_ids)}")
    return agent_ids[:2]


@pytest.fixture
def primary_agent_id(agent_ids: tuple[str, ...]) -> str:
    """The agent id of the first node -- where single-node scenarios pin their sessions."""
    return agent_ids[0]


@pytest.fixture(scope="session")
def node_pair(nodes: Sequence[Node]) -> tuple[Node, Node]:
    if len(nodes) < 2:
        _unavailable(f"needs two nodes; {ENV_NODES} names {len(nodes)}")
    return nodes[0], nodes[1]


@pytest.fixture
async def etcd(dataplane_config: DataplaneConfig) -> AsyncIterator[AsyncEtcd]:
    async with AsyncEtcd(
        dataplane_config.etcd_addr,
        dataplane_config.etcd_namespace,
        {ConfigScopes.GLOBAL: ""},
    ) as client:
        yield client


def _build_collectors(
    nodes: Sequence[Node],
    config: DataplaneConfig,
    etcd: AsyncEtcd | None,
) -> list[ResourceCollector]:
    collectors: list[ResourceCollector] = []
    for node in nodes:
        if config.runtime == "docker":
            runtime_collectors = list(docker_collectors(node))
            runtime_kernel_ids = DockerKernelContainerCollector(node).kernel_ids
        elif config.runtime == "containerd":
            containerd = ContainerdObjectCollector(
                node,
                address=config.containerd_address,
                namespace=config.containerd_namespace,
            )
            runtime_collectors = [containerd]
            runtime_kernel_ids = containerd.kernel_ids
        else:
            pytest.fail(f"unsupported BAI_DATAPLANE_RUNTIME: {config.runtime}", pytrace=False)

        async def live_kernel_ids(
            getter: Callable[[], Awaitable[set[str]]] = runtime_kernel_ids,
        ) -> set[str]:
            return await getter()

        collectors.extend([
            NetworkLinkCollector(node),
            IptablesRuleCollector(node),
            NeighbourCollector(node),
            XfrmCollector(node),
            StateFileCollector(node, dirs=config.state_dirs),
            MountCollector(node, prefixes=config.scratch_roots),
            ScratchDirCollector(node, roots=config.scratch_roots, live_ids=live_kernel_ids),
            *runtime_collectors,
        ])
    if etcd is not None:
        collectors.append(EtcdNetworkKeyCollector(etcd))
    return collectors


@pytest.fixture
async def leak_guard(
    nodes: Sequence[Node],
    dataplane_config: DataplaneConfig,
    etcd: AsyncEtcd,
    request: pytest.FixtureRequest,
) -> AsyncIterator[LeakGuard]:
    """Baseline before the test, assert back-to-baseline after it.

    The final assertion is skipped when the test body already failed: a scenario that failed
    halfway will of course leave resources behind, and reporting that as a second, louder failure
    buries the actual cause.
    """
    guard = LeakGuard(_build_collectors(nodes, dataplane_config, etcd))
    await guard.baseline()
    yield guard
    report = _call_reports.get(request.node.nodeid)
    if report is not None and report.failed:
        return
    await guard.assert_clean()


@pytest.fixture
async def session_driver(dataplane_config: DataplaneConfig) -> AsyncIterator[SessionDriver]:
    """A driver bound to a keypair reserved for this suite.

    Reserved, not shared: concurrent sessions are capped per keypair, so borrowing the developer's
    keypair means their running sessions decide whether the suite can start — which is how the
    first live run of this suite failed.
    """
    if not (dataplane_config.access_key and dataplane_config.secret_key):
        _unavailable(
            "BAI_DATAPLANE_ACCESS_KEY / _SECRET_KEY are unset; scenarios that create sessions "
            "need a keypair reserved for the suite"
        )
    # V2ClientRegistry, not BackendAIClientRegistry: the latter's `.session` is the v1 client,
    # which has no enqueue/terminate at all. The difference is invisible until the first live run.
    registry = await V2ClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(dataplane_config.manager_endpoint)),
        HMACAuth(
            access_key=dataplane_config.access_key,
            secret_key=dataplane_config.secret_key,
        ),
    )
    try:
        yield SessionDriver(registry.session)
    finally:
        await registry.close()


@pytest.fixture
async def spread_cpu(node_pair: tuple[Node, Node]) -> str:
    """A per-kernel CPU request that will not let two kernels share a node.

    `MULTI_NODE` says how a session is networked, not where it is placed: nothing in the scheduler
    makes two kernels of one session take two agents, so a cross-node scenario that does not ask
    for the spread gets whichever the selector's rotation happened to pick, and reports it as a
    skip. Asking for more than half a node is what leaves the scheduler no other choice.

    Derived from the pair's real CPU counts rather than written down, because a number that fits
    one rig stops scheduling on the next -- which is what a hardcoded ten did here.
    """
    counts = []
    for node in node_pair:
        result = await node.run(["nproc"])
        counts.append(int(result.stdout.strip()))
    # Two must not fit on the LARGER node, and one must still fit on the smaller. An unequal pair
    # can leave no such number, and then there is nothing to ask for: the scenario falls back to
    # the default request and skips if the selector packed it, which is what its skip says.
    wanted = max(counts) // 2 + 1
    return str(wanted) if wanted <= min(counts) else SessionSpec.cpu


@pytest.fixture
def session_spec(dataplane_config: DataplaneConfig) -> SessionSpec:
    """The image and project scenarios launch into.

    Both are site facts — an image UUID differs per deployment — so they are configured rather
    than discovered. Discovering them would make a scenario's placement depend on whatever the
    search happened to return first.
    """
    if not (dataplane_config.image_id and dataplane_config.project_id):
        _unavailable("BAI_DATAPLANE_IMAGE_ID / _PROJECT_ID are unset")
    return SessionSpec(
        image_id=UUID(dataplane_config.image_id),
        project_id=UUID(dataplane_config.project_id),
    )


@pytest.fixture
def agent_control(raw_nodes: Sequence[Node], dataplane_config: DataplaneConfig) -> AgentController:
    """Restart control for the first node's agent.

    Built on the *unsudo'd* node: the agent runs as the developer, so signalling and starting it
    must not go through sudo, or the agent comes up as root and the privnet refuses it (see
    `raw_nodes`). The port and pid lookups work as the developer too, since it owns the process.

    Skips unless a start command is configured: how an agent is supervised is a deployment fact,
    and guessing wrong kills the developer's agent without bringing it back.
    """
    config = AgentControlConfig(
        start_cmd=dataplane_config.agent_start_cmd or None,
        stop_cmd=dataplane_config.agent_stop_cmd or None,
        rpc_port=dataplane_config.agent_rpc_port,
    )
    if not config.configured:
        _unavailable(
            "BAI_DATAPLANE_AGENT_START_CMD is unset; restart scenarios cannot bring the agent back"
        )
    return AgentController(raw_nodes[0], config)


@pytest.fixture
def agent_gauges(
    nodes: Sequence[Node], dataplane_config: DataplaneConfig
) -> list[ProcessGaugeCollector]:
    return [
        ProcessGaugeCollector(node, pattern=dataplane_config.agent_process_pattern)
        for node in nodes
    ]


# nodeid -> the report of the test body itself. `leak_guard` reads this during its own teardown to
# tell "the scenario failed and of course left debris" from "the scenario passed but leaked".
_call_reports: dict[str, pytest.TestReport] = {}


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, pytest.TestReport, pytest.TestReport]:
    report = yield
    if report.skipped and _release_gate_required():
        reason = getattr(report, "longreprtext", "scenario skipped")
        report.outcome = "failed"
        report.longrepr = (
            f"{item.nodeid}: data-plane release gate forbids skipped or xfailed scenarios\n{reason}"
        )
    if report.when == "call":
        _call_reports[item.nodeid] = report
    elif report.when == "teardown":
        _call_reports.pop(item.nodeid, None)
    return report
