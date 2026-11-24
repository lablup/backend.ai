from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from decimal import Decimal

import pytest

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.data.agent.types import GPUDeviceAllocation, KernelGPUAllocation
from ai.backend.common.data.entity.kernel import KernelID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.defs import REDIS_STATISTICS_DB
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import AgentId, DeviceId, ValkeyTarget


@dataclass(frozen=True)
class _CachedGPUDevices:
    valkey_stat: ValkeyStatClient
    scanned_agent: AgentId
    undecodable_agent: AgentId
    unscanned_agent: AgentId
    gpu_devices: list[GPUDeviceAllocation]


class TestValkeyStatClient:
    @pytest.fixture
    async def test_valkey_stat(
        self, redis_container: tuple[str, HostPortPairModel]
    ) -> AsyncIterator[ValkeyStatClient]:
        hostport_pair: HostPortPairModel = redis_container[1]
        valkey_target = ValkeyTarget(
            addr=hostport_pair.address,
        )
        client = await ValkeyStatClient.create(
            valkey_target,
            human_readable_name="test.stat",
            db_id=REDIS_STATISTICS_DB,
        )
        try:
            yield client
        finally:
            await client.close()

    async def test_valkey_stat_expiration(self, test_valkey_stat: ValkeyStatClient) -> None:
        """Test key expiration functionality."""
        test_key = f"test-key-exp-{uuid.uuid4().hex[:8]}"
        test_value = b"test-value-exp"

        # Set with custom expiration
        await test_valkey_stat.set(test_key, test_value, expire_sec=1)

        # Verify key exists immediately
        result = await test_valkey_stat._get_raw(test_key)
        assert result == test_value

    async def test_valkey_stat_multiple_keys(self, test_valkey_stat: ValkeyStatClient) -> None:
        """Test multiple key operations."""
        test_keys = [f"test-key-{i}-{uuid.uuid4().hex[:8]}" for i in range(3)]
        test_values = [f"test-value-{i}".encode() for i in range(3)]

        # Set multiple keys
        key_value_map = dict(zip(test_keys, test_values, strict=True))
        await test_valkey_stat.set_multiple_keys(key_value_map)

        # Get multiple keys
        results = await test_valkey_stat._get_multiple_keys(test_keys)
        assert len(results) == len(test_keys)
        for i, result in enumerate(results):
            assert result == test_values[i]

        # Clean up
        deleted_count = await test_valkey_stat.delete(test_keys)
        assert deleted_count == len(test_keys)

    @pytest.fixture
    async def cached_gpu_devices(self, test_valkey_stat: ValkeyStatClient) -> _CachedGPUDevices:
        run_id = uuid.uuid4().hex[:8]
        cached = _CachedGPUDevices(
            valkey_stat=test_valkey_stat,
            scanned_agent=AgentId(f"scanned-{run_id}"),
            undecodable_agent=AgentId(f"undecodable-{run_id}"),
            unscanned_agent=AgentId(f"unscanned-{run_id}"),
            gpu_devices=[
                GPUDeviceAllocation(
                    device_id=DeviceId("GPU-00000000-0000-0000-0000-000000000001"),
                    device_index=None,
                    allocated_ratio=Decimal("0.3333"),
                    kernel_allocations=[
                        KernelGPUAllocation(
                            kernel_id=KernelID(uuid.uuid4()),
                            session_id=SessionID(uuid.uuid4()),
                            allocated_ratio=Decimal("0.3333"),
                        ),
                    ],
                ),
            ],
        )
        await test_valkey_stat.set(
            f"gpu_devices.{cached.undecodable_agent}", b'[{"device_id": "GPU-1"}]'
        )
        return cached

    async def test_gpu_devices_batch_answers_per_agent(
        self, cached_gpu_devices: _CachedGPUDevices
    ) -> None:
        await cached_gpu_devices.valkey_stat.set_gpu_devices(
            cached_gpu_devices.scanned_agent, cached_gpu_devices.gpu_devices
        )

        loaded = await cached_gpu_devices.valkey_stat.get_gpu_devices_batch([
            cached_gpu_devices.scanned_agent,
            cached_gpu_devices.undecodable_agent,
            cached_gpu_devices.unscanned_agent,
        ])

        assert loaded == [cached_gpu_devices.gpu_devices, None, None]
