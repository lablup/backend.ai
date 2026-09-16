import stat
from pathlib import Path

import pytest

from ai.backend.accelerator.dax.config import DAXPluginConfig
from ai.backend.accelerator.dax.discovery import (
    DiscoveryResult,
    ExcludedReason,
    discover_devices,
)

from .conftest import ALIGN, FAKE_GID, FakeStat, FakeSysfs


def _reasons(result: DiscoveryResult) -> dict[str, ExcludedReason | None]:
    return {info.name: info.excluded_reason for info in result.excluded}


class TestDiscoverAdmitted:
    def test_cxl_device_gets_serial_identity(
        self, fake_sysfs: FakeSysfs, fake_stat: FakeStat
    ) -> None:
        fake_sysfs.add_cxl_device("dax0.0", serials=("0x1a2b",), numa_node=1, target_node=2)

        result = discover_devices(DAXPluginConfig(sysfs_root=fake_sysfs.root), fake_stat)

        assert result.excluded == []
        [info] = result.admitted
        assert info.device_id == "dax-0x1a2b"
        assert info.path == "/dev/dax0.0"
        assert info.region == "region0"
        assert info.serials == ("0x1a2b",)
        assert (info.size, info.align, info.numa_node, info.target_node) == (
            64 * ALIGN,
            ALIGN,
            1,
            2,
        )
        assert info.driver == "device_dax"
        assert info.gid == FAKE_GID

    def test_two_way_region_joins_serials_in_target_order(
        self, fake_sysfs: FakeSysfs, fake_stat: FakeStat
    ) -> None:
        fake_sysfs.add_cxl_device("dax0.0", serials=("0x1", "0x2"))

        result = discover_devices(DAXPluginConfig(sysfs_root=fake_sysfs.root), fake_stat)

        [info] = result.admitted
        assert info.device_id == "dax-0x1+0x2"

    def test_zero_size_seed_sibling_does_not_split(
        self, fake_sysfs: FakeSysfs, fake_stat: FakeStat
    ) -> None:
        fake_sysfs.add_cxl_device("dax0.0")
        # The kernel refuses to bind a zero-size device to any dax driver.
        fake_sysfs.add_cxl_device("dax0.1", size=0, driver=None)

        result = discover_devices(DAXPluginConfig(sysfs_root=fake_sysfs.root), fake_stat)

        assert [info.name for info in result.admitted] == ["dax0.0"]
        assert _reasons(result) == {"dax0.1": ExcludedReason.NOT_DEVICE_DAX}

    @pytest.mark.parametrize("entry", ["dax0.0", "dax-0x1a2b"], ids=["by-name", "by-id"])
    def test_allowlist_matches_name_or_id(
        self, fake_sysfs: FakeSysfs, fake_stat: FakeStat, entry: str
    ) -> None:
        fake_sysfs.add_cxl_device("dax0.0", serials=("0x1a2b",))
        fake_sysfs.add_cxl_device("dax1.0", region="region1", serials=("0x3c4d",))

        result = discover_devices(
            DAXPluginConfig(sysfs_root=fake_sysfs.root, allowlist=[entry]), fake_stat
        )

        assert [info.name for info in result.admitted] == ["dax0.0"]
        assert _reasons(result) == {"dax1.0": ExcludedReason.NOT_ALLOWLISTED}


class TestDiscoverExcluded:
    @pytest.mark.parametrize("driver", [None, "dax_hmem"], ids=["unbound", "other-driver"])
    def test_not_device_dax(
        self, fake_sysfs: FakeSysfs, fake_stat: FakeStat, driver: str | None
    ) -> None:
        fake_sysfs.add_cxl_device("dax0.0", driver=driver)

        result = discover_devices(DAXPluginConfig(sysfs_root=fake_sysfs.root), fake_stat)

        assert _reasons(result) == {"dax0.0": ExcludedReason.NOT_DEVICE_DAX}

    def test_not_cxl(self, fake_sysfs: FakeSysfs, fake_stat: FakeStat) -> None:
        fake_sysfs.add_non_cxl_device("dax5.0")

        result = discover_devices(DAXPluginConfig(sysfs_root=fake_sysfs.root), fake_stat)

        assert _reasons(result) == {"dax5.0": ExcludedReason.NOT_CXL}

    def test_split_region(self, fake_sysfs: FakeSysfs, fake_stat: FakeStat) -> None:
        fake_sysfs.add_cxl_device("dax0.0", size=32 * ALIGN)
        fake_sysfs.add_cxl_device("dax0.1", size=32 * ALIGN)

        result = discover_devices(DAXPluginConfig(sysfs_root=fake_sysfs.root), fake_stat)

        assert _reasons(result) == {
            "dax0.0": ExcludedReason.SPLIT_REGION,
            "dax0.1": ExcludedReason.SPLIT_REGION,
        }

    def test_no_serial(self, fake_sysfs: FakeSysfs, fake_stat: FakeStat) -> None:
        fake_sysfs.add_cxl_device("dax0.0", serials=("",))

        result = discover_devices(DAXPluginConfig(sysfs_root=fake_sysfs.root), fake_stat)

        assert _reasons(result) == {"dax0.0": ExcludedReason.NO_SERIAL}

    def test_not_allowlisted(self, fake_sysfs: FakeSysfs, fake_stat: FakeStat) -> None:
        fake_sysfs.add_cxl_device("dax0.0")

        result = discover_devices(
            DAXPluginConfig(sysfs_root=fake_sysfs.root, allowlist=["dax-0xffff"]), fake_stat
        )

        assert _reasons(result) == {"dax0.0": ExcludedReason.NOT_ALLOWLISTED}

    def test_node_missing(self, fake_sysfs: FakeSysfs, fake_stat: FakeStat) -> None:
        fake_sysfs.add_cxl_device("dax0.0")
        fake_stat.missing.add("dax0.0")

        result = discover_devices(DAXPluginConfig(sysfs_root=fake_sysfs.root), fake_stat)

        assert _reasons(result) == {"dax0.0": ExcludedReason.NODE_MISSING}

    @pytest.mark.parametrize(
        "mode",
        [stat.S_IFREG | 0o660, stat.S_IFCHR | 0o600, stat.S_IFCHR | 0o666],
        ids=["not-char", "no-group-rw", "other-writable"],
    )
    def test_node_permissions(self, fake_sysfs: FakeSysfs, fake_stat: FakeStat, mode: int) -> None:
        fake_sysfs.add_cxl_device("dax0.0")
        fake_stat.modes["dax0.0"] = mode

        result = discover_devices(DAXPluginConfig(sysfs_root=fake_sysfs.root), fake_stat)

        assert _reasons(result) == {"dax0.0": ExcludedReason.NODE_PERMISSIONS}

    def test_heterogeneous_size(self, fake_sysfs: FakeSysfs, fake_stat: FakeStat) -> None:
        fake_sysfs.add_cxl_device("dax0.0", size=64 * ALIGN)
        fake_sysfs.add_cxl_device("dax1.0", region="region1", serials=("0x3c4d",), size=32 * ALIGN)

        result = discover_devices(DAXPluginConfig(sysfs_root=fake_sysfs.root), fake_stat)

        assert result.admitted == []
        assert _reasons(result) == {
            "dax0.0": ExcludedReason.HETEROGENEOUS_SIZE,
            "dax1.0": ExcludedReason.HETEROGENEOUS_SIZE,
        }

    def test_heterogeneous_size_is_checked_after_allowlist(
        self, fake_sysfs: FakeSysfs, fake_stat: FakeStat
    ) -> None:
        fake_sysfs.add_cxl_device("dax0.0", size=64 * ALIGN)
        fake_sysfs.add_cxl_device("dax1.0", region="region1", serials=("0x3c4d",), size=32 * ALIGN)

        result = discover_devices(
            DAXPluginConfig(sysfs_root=fake_sysfs.root, allowlist=["dax0.0"]), fake_stat
        )

        assert [info.name for info in result.admitted] == ["dax0.0"]
        assert _reasons(result) == {"dax1.0": ExcludedReason.NOT_ALLOWLISTED}


class TestDiscoverEdge:
    def test_missing_root_yields_no_device(self, tmp_path: Path, fake_stat: FakeStat) -> None:
        result = discover_devices(DAXPluginConfig(sysfs_root=tmp_path / "nowhere"), fake_stat)

        assert (list(result.admitted), list(result.excluded)) == ([], [])

    def test_allow_non_cxl_uses_name_identity(
        self, fake_sysfs: FakeSysfs, fake_stat: FakeStat
    ) -> None:
        fake_sysfs.add_non_cxl_device("dax0.0")

        result = discover_devices(
            DAXPluginConfig(sysfs_root=fake_sysfs.root, allow_non_cxl=True), fake_stat
        )

        [info] = result.admitted
        assert info.device_id == "dax-dax0.0"
        assert info.serials == ()

    def test_allow_non_cxl_admits_equal_size_cxl_pair(
        self, fake_sysfs: FakeSysfs, fake_stat: FakeStat
    ) -> None:
        fake_sysfs.add_cxl_device("dax0.0", serials=("0x1a2b",), size=64 * ALIGN, align=ALIGN)
        fake_sysfs.add_non_cxl_device("dax1.0", size=64 * ALIGN, align=ALIGN)

        result = discover_devices(
            DAXPluginConfig(sysfs_root=fake_sysfs.root, allow_non_cxl=True), fake_stat
        )

        assert result.excluded == []
        cxl, non_cxl = result.admitted
        assert (cxl.name, cxl.device_id, cxl.region, cxl.serials) == (
            "dax0.0",
            "dax-0x1a2b",
            "region0",
            ("0x1a2b",),
        )
        # A non-CXL device reports its dax region directory, not a CXL region.
        assert (non_cxl.name, non_cxl.device_id, non_cxl.region, non_cxl.serials) == (
            "dax1.0",
            "dax-dax1.0",
            "dax_hmem0",
            (),
        )
        assert (cxl.size, cxl.align) == (non_cxl.size, non_cxl.align) == (64 * ALIGN, ALIGN)

    def test_mock_skips_node_checks(self, fake_sysfs: FakeSysfs, fake_stat: FakeStat) -> None:
        fake_sysfs.add_cxl_device("dax0.0")
        fake_stat.missing.add("dax0.0")

        result = discover_devices(DAXPluginConfig(sysfs_root=fake_sysfs.root, mock=True), fake_stat)

        [info] = result.admitted
        assert info.name == "dax0.0"
        assert info.gid is None
