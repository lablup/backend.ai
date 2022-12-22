from decimal import Decimal

import pytest

from ai.backend.agent.kubernetes.intrinsic import CPUPlugin, MemoryPlugin
from ai.backend.agent.stats import Measurement, MetricKey


@pytest.mark.asyncio
async def test_gather_node_cpu_measures(mocker):
    async def mock_list_node(obj):
        mock_raw_data = {"items": [{"metadata": {"name": "node1", "uid": "uid1"}}]}
        mock_node_list = mocker.Mock()
        mock_node_list.to_dict = mocker.Mock()
        mock_node_list.to_dict.return_value = mock_raw_data
        return mock_node_list

    async def mock_connect_get_node_proxy_with_path(obj, name, path):
        assert name == "node1"
        return "node_cpu_usage_seconds_total 7886.025125937 1671604484613"

    mocker.patch("kubernetes_asyncio.config.load_kube_config")
    mocker.patch("kubernetes_asyncio.client.CoreV1Api.list_node", mock_list_node)
    mocker.patch(
        "kubernetes_asyncio.client.CoreV1Api.connect_get_node_proxy_with_path",
        mock_connect_get_node_proxy_with_path,
    )
    ctx = mocker.Mock()
    ctx.update_timestamp.return_value = (1, 1)
    cpu_plugin = CPUPlugin
    node_measures = await cpu_plugin.gather_node_measures(cpu_plugin, ctx)

    assert node_measures[0].per_node.value == Decimal("7886025")
    assert node_measures[0].per_node.capacity == Decimal("1000")
    assert node_measures[0].per_device == {"uid1": Measurement(Decimal("7886025"), Decimal("1000"))}


@pytest.mark.asyncio
async def test_gather_node_mem_measures(mocker):
    async def mock_list_node(obj):
        mock_raw_data = {
            "items": [
                {
                    "metadata": {"name": "node1", "uid": "uid1"},
                    "status": {
                        "capacity": {"ephemeral-storage": "40585520Ki", "memory": "8105828Ki"},
                        "allocatable": {"ephemeral-storage": "37403615171"},
                    },
                }
            ]
        }
        mock_node_list = mocker.Mock()
        mock_node_list.to_dict = mocker.Mock()
        mock_node_list.to_dict.return_value = mock_raw_data
        return mock_node_list

    async def mock_connect_get_node_proxy_with_path(obj, name, path):
        assert name == "node1"
        if path == "metrics/resource":
            return "node_memory_working_set_bytes 3.091173376e+09 1671673890797"
        return """container_network_receive_bytes_total{container="",id="/",image="",interface="br-7c9cc23793ee",name="",namespace="",pod=""} 0 1671675240542
container_network_receive_bytes_total{container="",id="/",image="",interface="cni0",name="",namespace="",pod=""} 438433 1671675240542
container_network_receive_bytes_total{container="",id="/",image="",interface="ens33",name="",namespace="",pod=""} 5.124159e+06 1671675240542
container_network_receive_bytes_total{container="",id="/",image="",interface="flannel.1",name="",namespace="",pod=""} 0 1671675240542
container_network_transmit_bytes_total{container="",id="/",image="",interface="br-7c9cc23793ee",name="",namespace="",pod=""} 28315 1671675240542
container_network_transmit_bytes_total{container="",id="/",image="",interface="cni0",name="",namespace="",pod=""} 603123 1671675240542
container_network_transmit_bytes_total{container="",id="/",image="",interface="ens33",name="",namespace="",pod=""} 4.186006e+06 1671675240542
container_network_transmit_bytes_total{container="",id="/",image="",interface="flannel.1",name="",namespace="",pod=""} 0 1671675240542"""

    mocker.patch("kubernetes_asyncio.config.load_kube_config")
    mocker.patch("kubernetes_asyncio.client.CoreV1Api.list_node", mock_list_node)
    mocker.patch(
        "kubernetes_asyncio.client.CoreV1Api.connect_get_node_proxy_with_path",
        mock_connect_get_node_proxy_with_path,
    )
    ctx = mocker.Mock()
    mem_plugin = MemoryPlugin
    node_measures = await mem_plugin.gather_node_measures(mem_plugin, ctx)

    for node_measure in node_measures:
        if node_measure.key == MetricKey("mem"):
            assert node_measure.per_node.value == Decimal("3091173376")
            assert node_measure.per_node.capacity == Decimal("8300367872")
            assert node_measure.per_device == {
                "root": Measurement(Decimal("3091173376"), Decimal("8300367872"))
            }
        elif node_measure.key == MetricKey("disk"):
            assert node_measure.per_node.value == Decimal("4155957309")
            assert node_measure.per_node.capacity == Decimal("41559572480")
            assert node_measure.per_device == {
                "uid1": Measurement(Decimal("4155957309"), Decimal("41559572480"))
            }
        elif node_measure.key == MetricKey("net_rx"):
            assert node_measure.per_node.value == Decimal("5562592")
            assert node_measure.per_device == {"node": Measurement(Decimal("5562592"))}
        elif node_measure.key == MetricKey("net_tx"):
            assert node_measure.per_node.value == Decimal("4817444")
            assert node_measure.per_device == {"node": Measurement(Decimal("4817444"))}
