"""Fixtures for the data-plane suite.

The whole suite is opt-in through ``BAI_DATAPLANE_NODES``. With it unset, every host-touching
fixture skips and only the harness self-check runs — `pants test ::` on a laptop must not start
poking at iptables.
"""

from __future__ import annotations

import asyncio
import os
import shlex
from collections.abc import AsyncIterator, Generator, Sequence
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
from ai.backend.testutils.dataplane.collectors.docker_objects import DockerKernelContainerCollector
from ai.backend.testutils.dataplane.collectors.etcd_keys import EtcdNetworkKeyCollector
from ai.backend.testutils.dataplane.collectors.gauges import ProcessGaugeCollector
from ai.backend.testutils.dataplane.collectors.host import (
    IptablesRuleCollector,
    MountCollector,
    NeighbourCollector,
    NetworkLinkCollector,
    ScratchDirCollector,
    StateFileCollector,
)
from ai.backend.testutils.dataplane.guard import LeakGuard
from ai.backend.testutils.dataplane.nodes import Node, SudoNode, parse_node_specs
from ai.backend.testutils.dataplane.session import SessionDriver, SessionSpec

ENV_NODES = "BAI_DATAPLANE_NODES"


@dataclass(frozen=True)
class DataplaneConfig:
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

    @property
    def state_dirs(self) -> tuple[str, ...]:
        return (
            f"{self.state_root}/net-local-subnet",
            f"{self.state_root}/net-ipam",
        )


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


@pytest.fixture(scope="session")
def dataplane_config() -> DataplaneConfig:
    host, _, port = _env("BAI_DATAPLANE_ETCD_ADDR", "127.0.0.1:8120").rpartition(":")
    return DataplaneConfig(
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
    )


@pytest.fixture(scope="session")
def nodes(dataplane_config: DataplaneConfig) -> Sequence[Node]:
    raw = os.environ.get(ENV_NODES, "").strip()
    if not raw:
        pytest.skip(f"{ENV_NODES} is unset; data-plane tests need a host to run against")
    parsed = parse_node_specs(raw)
    if dataplane_config.use_sudo:
        return [SudoNode(node) for node in parsed]
    return parsed


@pytest.fixture(scope="session")
def node(nodes: Sequence[Node]) -> Node:
    return nodes[0]


@pytest.fixture(scope="session")
def node_pair(nodes: Sequence[Node]) -> tuple[Node, Node]:
    if len(nodes) < 2:
        pytest.skip(f"needs two nodes; {ENV_NODES} names {len(nodes)}")
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
        containerd = ContainerdObjectCollector(
            node,
            address=config.containerd_address,
            namespace=config.containerd_namespace,
        )
        docker = DockerKernelContainerCollector(node)

        async def live_kernel_ids(
            containerd: ContainerdObjectCollector = containerd,
            docker: DockerKernelContainerCollector = docker,
        ) -> set[str]:
            # The union of both runtimes, not just the configured one: a scratch directory is
            # orphaned only when *nothing* still has a container record for it, and a host that
            # has run both backends holds scratches from each.
            owned = await asyncio.gather(containerd.kernel_ids(), docker.kernel_ids())
            return set().union(*owned)

        collectors.extend([
            NetworkLinkCollector(node),
            IptablesRuleCollector(node),
            NeighbourCollector(node),
            StateFileCollector(node, dirs=config.state_dirs),
            MountCollector(node, prefixes=config.scratch_roots),
            ScratchDirCollector(node, roots=config.scratch_roots, live_ids=live_kernel_ids),
            containerd,
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
        pytest.skip(
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
def session_spec(dataplane_config: DataplaneConfig) -> SessionSpec:
    """The image and project scenarios launch into.

    Both are site facts — an image UUID differs per deployment — so they are configured rather
    than discovered. Discovering them would make a scenario's placement depend on whatever the
    search happened to return first.
    """
    if not (dataplane_config.image_id and dataplane_config.project_id):
        pytest.skip("BAI_DATAPLANE_IMAGE_ID / _PROJECT_ID are unset")
    return SessionSpec(
        image_id=UUID(dataplane_config.image_id),
        project_id=UUID(dataplane_config.project_id),
    )


@pytest.fixture
def agent_control(nodes: Sequence[Node], dataplane_config: DataplaneConfig) -> AgentController:
    """Restart control for the first node's agent.

    Skips unless a start command is configured: how an agent is supervised is a deployment fact,
    and guessing wrong kills the developer's agent without bringing it back.
    """
    config = AgentControlConfig(
        start_cmd=dataplane_config.agent_start_cmd or None,
        stop_cmd=dataplane_config.agent_stop_cmd or None,
        process_pattern=dataplane_config.agent_process_pattern,
        rpc_port=dataplane_config.agent_rpc_port,
    )
    if not config.configured:
        pytest.skip(
            "BAI_DATAPLANE_AGENT_START_CMD is unset; restart scenarios cannot bring the agent back"
        )
    return AgentController(nodes[0], config)


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
    if report.when == "call":
        _call_reports[item.nodeid] = report
    elif report.when == "teardown":
        _call_reports.pop(item.nodeid, None)
    return report
