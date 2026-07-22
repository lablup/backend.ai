"""Fixtures for the data-plane suite.

The whole suite is opt-in through ``BAI_DATAPLANE_NODES``. With it unset, every host-touching
fixture skips and only the harness self-check runs — `pants test ::` on a laptop must not start
poking at iptables.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator, Generator, Sequence
from dataclasses import dataclass, field

import pytest

from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.types import HostPortPair
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
