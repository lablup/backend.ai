"""Component tests: Prometheus scrapes model-service targets after relabel rewrite."""

from __future__ import annotations

import asyncio
import secrets
import textwrap
import time
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from aiohttp import web
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

from ai.backend.common.clients.http_client.client_pool import (
    ClientPool,
    tcp_client_session_factory,
)
from ai.backend.common.clients.prometheus import (
    LabelMatcher,
    MetricPreset,
)
from ai.backend.common.dto.clients.prometheus import PrometheusResponse
from ai.backend.common.service_discovery.service_discovery import MODEL_SERVICE_GROUP
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.manager.clients.prometheus import (
    ContainerLiveStatQueryBuilder,
    ContainerMetricQueryBuilder,
    PrometheusClient,
)
from ai.backend.testutils.pants import get_parallel_slot

# ---------------------------------------------------------------------------
# Fixtures: mock HTTP servers (SD endpoint + metrics endpoint)
# ---------------------------------------------------------------------------


@pytest.fixture
async def mock_metrics_server() -> AsyncIterator[int]:
    """A minimal /metrics endpoint that Prometheus can scrape."""

    async def handle_metrics(_request: web.Request) -> web.Response:
        return web.Response(
            text=("# HELP test_gauge A test gauge\n# TYPE test_gauge gauge\ntest_gauge 42\n"),
            content_type="text/plain",
        )

    app = web.Application()
    app.router.add_get("/metrics", handle_metrics)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]  # type: ignore[union-attr]
    try:
        yield port
    finally:
        await runner.cleanup()


@pytest.fixture
async def mock_sd_server(mock_metrics_server: int) -> AsyncIterator[int]:
    """HTTP SD endpoint returning a model-service target with Docker-internal IP.

    The target address uses 127.0.0.1 (simulating a Docker-internal IP),
    which will be rewritten by relabel_configs to host.docker.internal.
    The actual metrics server runs on the same port, reachable via
    host.docker.internal from the Prometheus container.
    """

    async def handle_sd(_request: web.Request) -> web.Response:
        # 127.0.0.1 simulates a Docker-internal IP that is unreachable
        # from the Prometheus container. The relabel rule will rewrite it
        # to host.docker.internal, which IS reachable.
        return web.json_response([
            {
                "targets": [f"127.0.0.1:{mock_metrics_server}"],
                "labels": {
                    "service_group": MODEL_SERVICE_GROUP,
                    "service_id": "test-model-svc-001",
                    "display_name": "test-model",
                    "version": "1.0",
                },
            },
        ])

    app = web.Application()
    app.router.add_get("/metrics/service_discovery", handle_sd)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]  # type: ignore[union-attr]
    try:
        yield port
    finally:
        await runner.cleanup()


# ---------------------------------------------------------------------------
# Fixtures: Prometheus container with custom relabel config
# ---------------------------------------------------------------------------


@pytest.fixture
def prometheus_config_yaml(mock_sd_server: int) -> str:
    """Prometheus config YAML with relabel_configs for loopback address rewrite."""
    return textwrap.dedent(f"""\
        global:
          scrape_interval: 2s

        scrape_configs:
          - job_name: 'http-sd'
            scheme: 'http'
            http_sd_configs:
              - url: 'http://host.docker.internal:{mock_sd_server}/metrics/service_discovery'
                refresh_interval: '2s'
            relabel_configs:
              - source_labels: [__address__]
                regex: '127\\.0\\.0\\.1(.*)'
                target_label: __address__
                replacement: 'host.docker.internal${{1}}'
    """)


@pytest.fixture
def prometheus_config_with_relabel(
    prometheus_config_yaml: str,
    tmp_path: Path,
) -> Path:
    """Write prometheus config to a temp file for container volume mount."""
    config_path = tmp_path / "prometheus.yml"
    config_path.write_text(prometheus_config_yaml)
    return config_path


@pytest.fixture
def prometheus_with_relabel(
    prometheus_config_with_relabel: Path,
) -> Iterator[HostPortPairModel]:
    """Spawn Prometheus container with relabel_configs mounted."""
    random_id = secrets.token_hex(8)
    container = (
        DockerContainer("prom/prometheus:v2.53.0")
        .with_name(f"test--prom-relabel-slot-{get_parallel_slot()}-{random_id}")
        .with_exposed_ports(9090)
        .with_volume_mapping(
            str(prometheus_config_with_relabel),
            "/etc/prometheus/prometheus.yml",
            mode="ro",
        )
        .with_kwargs(
            tmpfs={"/prometheus": "rw,uid=65534,gid=65534"},
            extra_hosts={"host.docker.internal": "host-gateway"},
        )
        .with_command(
            "--config.file=/etc/prometheus/prometheus.yml "
            "--storage.tsdb.path=/prometheus "
            "--storage.tsdb.retention.time=1h"
        )
    )
    container.start()
    published_port = int(container.get_exposed_port(9090))
    try:
        wait_for_logs(container, "Server is ready to receive web requests.", timeout=30)
        time.sleep(0.5)
        yield HostPortPairModel(host="127.0.0.1", port=published_port)
    finally:
        container.stop()


@pytest.fixture
async def prometheus_client_with_relabel(
    prometheus_with_relabel: HostPortPairModel,
) -> AsyncIterator[PrometheusClient]:
    pool = ClientPool(tcp_client_session_factory)
    client = PrometheusClient(
        endpoint=f"http://{prometheus_with_relabel.host}:{prometheus_with_relabel.port}/api/v1/",
        client_pool=pool,
        container_metric_query_builder=ContainerMetricQueryBuilder("1m"),
        container_live_stat_query_builder=ContainerLiveStatQueryBuilder("1m"),
    )
    try:
        yield client
    finally:
        await pool.close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.fixture
def up_model_service_preset() -> MetricPreset:
    return MetricPreset(
        template="up{{{labels}}}",
        labels={"service_group": LabelMatcher.exact(MODEL_SERVICE_GROUP)},
        group_by=frozenset(),
    )


class TestLoopbackRelabelScrape:
    """Verify Prometheus scrapes model-service targets after relabel rewrite."""

    async def test_prometheus_scrapes_model_service_after_relabel(
        self,
        prometheus_client_with_relabel: PrometheusClient,
        up_model_service_preset: MetricPreset,
    ) -> None:
        """Model-service metrics are scraped via the relabel-rewritten address."""
        # Prometheus needs time to discover targets and scrape
        max_attempts = 15
        result: PrometheusResponse | None = None

        for _ in range(max_attempts):
            await asyncio.sleep(2)
            result = await prometheus_client_with_relabel._query_instant(up_model_service_preset)
            if result.data.result and result.data.result[0].values[-1][1] == "1":
                break

        assert result is not None
        assert len(result.data.result) > 0, (
            "Prometheus failed to scrape model-service target after relabel rewrite"
        )
        metric = result.data.result[0]
        assert metric.values[-1][1] == "1"
