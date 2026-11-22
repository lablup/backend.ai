from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from ai.backend.common.types import DeviceId, SlotName
from ai.backend.dra.bridge import parse_quantity
from ai.backend.dra.errors import InvalidQuantityError, IsolationUnavailableError
from ai.backend.dra.host.isolation import (
    BaiHook,
    HamiCore,
    IsolationKind,
    isolation_provider,
    limit_from_shares,
    shares_value,
)

GIB = 1024**3


class TestLimitFromShares:
    def test_memory_and_sms_follow_the_share_units(self) -> None:
        limit = limit_from_shares(0, 150, 2 * GIB, 8, 132)
        # 1.5 shares → 3 GiB and 12 SMs → ceil(12 / 132 × 100) = 10 %.
        assert (limit.memory_bytes, limit.sm_percent) == (3 * GIB, 10)

    def test_a_small_share_gets_the_minimum_sm_count(self) -> None:
        # 0.1 share → 0.8 SMs, raised to MIN_SMP_COUNT (4) → ceil(4 / 132 × 100) = 4 %.
        assert limit_from_shares(0, 10, 2 * GIB, 8, 132).sm_percent == 4

    def test_the_sm_limit_is_capped_at_100(self) -> None:
        assert limit_from_shares(1, 2000, 2 * GIB, 8, 132).sm_percent == 100


class TestParseQuantity:
    @pytest.mark.parametrize(
        ("text", "value"),
        [("150", 150), ("1.5k", 1500), ("2Ki", 2048), ("1e3", 1000), ("500m", Decimal("0.5"))],
    )
    def test_kubernetes_quantities(self, text: str, value: Decimal | int) -> None:
        assert parse_quantity(text) == value

    def test_garbage_is_refused(self) -> None:
        with pytest.raises(InvalidQuantityError):
            parse_quantity("lots")


class TestIsolationProvider:
    def test_hami_core_needs_its_directory(self) -> None:
        with pytest.raises(IsolationUnavailableError):
            isolation_provider(IsolationKind.HAMI_CORE)

    def test_each_kind_has_its_provider(self) -> None:
        hami = isolation_provider(IsolationKind.HAMI_CORE, hami_lib_dir=Path("/x"))
        assert isinstance(hami, HamiCore)
        assert isinstance(isolation_provider(IsolationKind.BAI_HOOK), BaiHook)
        assert isolation_provider(IsolationKind.NONE) is None


class TestSharesValue:
    def test_only_share_slots_in_the_agent_format(self) -> None:
        alloc = {
            SlotName("cuda.shares"): {
                DeviceId("GPU-a"): Decimal("0.5"),
                DeviceId("GPU-b"): Decimal(2),
            },
            SlotName("cuda.device"): {DeviceId("GPU-c"): Decimal(1)},
        }
        assert shares_value(alloc) == "GPU-a:0.5,GPU-b:2"
