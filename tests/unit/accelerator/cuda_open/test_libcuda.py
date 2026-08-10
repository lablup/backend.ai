from __future__ import annotations

import ctypes
from collections.abc import Callable, Iterator
from typing import Any

import pytest

from ai.backend.accelerator.cuda_open.nvidia import CudaDeviceProps, LibraryError, libcuda

FAKE_UUID = bytes(range(16))
FAKE_TOTAL_MEM = 80 * 1024**3  # deliberately above the legacy 32-bit ABI limit
FAKE_MP_COUNT = 108
FAKE_PCI_BUS_ID = b"0000:AF:00.0"
FAKE_DEVICE_NAME = b"Fake GPU"
FAKE_DRIVER_VERSION = 12040  # decodes to (12, 4)


class FakeCudaLib:
    """A stand-in for the libcuda CDLL handle.

    Symbols listed in ``missing_symbols`` raise ``AttributeError`` on access
    (mimicking a driver that lacks them), and symbols listed in ``error_rcs``
    return the given nonzero CUresult code. All other functions write
    deterministic fake values into the ``ctypes.byref`` output arguments and
    return 0. Every invocation is recorded in ``calls``.
    """

    calls: list[str]

    def __init__(
        self,
        *,
        missing_symbols: frozenset[str] = frozenset(),
        error_rcs: dict[str, int] | None = None,
    ) -> None:
        self.calls = []
        self._missing_symbols = missing_symbols
        self._error_rcs = error_rcs or {}
        self._impls: dict[str, Callable[..., int]] = {
            "cuInit": self._cu_init,
            "cuDriverGetVersion": self._cu_driver_get_version,
            "cuDeviceGetCount": self._cu_device_get_count,
            "cuDeviceGet": self._cu_device_get,
            "cuDeviceGetName": self._cu_device_get_name,
            "cuDeviceGetUuid_v2": self._cu_device_get_uuid,
            "cuDeviceGetUuid": self._cu_device_get_uuid,
            "cuDeviceTotalMem_v2": self._cu_device_total_mem,
            "cuDeviceGetAttribute": self._cu_device_get_attribute,
            "cuDeviceGetPCIBusId": self._cu_device_get_pci_bus_id,
        }

    def __getattr__(self, name: str) -> Callable[..., int]:
        if name.startswith("_"):
            raise AttributeError(name)
        if name in self._missing_symbols:
            raise AttributeError(name)
        impl = self._impls.get(name)
        if impl is None:
            raise AttributeError(name)

        def wrapper(*args: Any) -> int:
            self.calls.append(name)
            rc = self._error_rcs.get(name)
            if rc is not None:
                return rc
            return impl(*args)

        return wrapper

    @staticmethod
    def _cu_init(flags: int) -> int:
        return 0

    @staticmethod
    def _cu_driver_get_version(ver_ref: Any) -> int:
        ver_ref._obj.value = FAKE_DRIVER_VERSION
        return 0

    @staticmethod
    def _cu_device_get_count(count_ref: Any) -> int:
        count_ref._obj.value = 1
        return 0

    @staticmethod
    def _cu_device_get(device_ref: Any, ordinal: int) -> int:
        device_ref._obj.value = ordinal
        return 0

    @staticmethod
    def _cu_device_get_name(buf_ref: Any, size: int, device: int) -> int:
        buf_ref._obj.value = FAKE_DEVICE_NAME
        return 0

    @staticmethod
    def _cu_device_get_uuid(buf_ref: Any, device: int) -> int:
        ctypes.memmove(buf_ref._obj, FAKE_UUID, len(FAKE_UUID))
        return 0

    @staticmethod
    def _cu_device_total_mem(mem_ref: Any, device: int) -> int:
        mem_ref._obj.value = FAKE_TOTAL_MEM
        return 0

    @staticmethod
    def _cu_device_get_attribute(value_ref: Any, attrib: int, device: int) -> int:
        value_ref._obj.value = FAKE_MP_COUNT
        return 0

    @staticmethod
    def _cu_device_get_pci_bus_id(buf_ref: Any, size: int, device: int) -> int:
        buf_ref._obj.value = FAKE_PCI_BUS_ID
        return 0


@pytest.fixture(autouse=True)
def reset_libcuda_caches(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Reset the class-level caches so tests never observe each other's state."""
    monkeypatch.setattr(libcuda, "_lib", None)
    monkeypatch.setattr(libcuda, "_initialized", False)
    monkeypatch.setattr(libcuda, "_version", (0, 0))
    monkeypatch.setattr(libcuda, "_init_error", None)
    yield


def _install_fake_lib(monkeypatch: pytest.MonkeyPatch, fake_lib: FakeCudaLib) -> None:
    monkeypatch.setattr(libcuda, "_lib", fake_lib)


class TestGetDeviceProps:
    """Tests for libcuda.get_device_props."""

    def test_normal_path_returns_typed_props(self, monkeypatch: pytest.MonkeyPatch) -> None:
        fake_lib = FakeCudaLib()
        _install_fake_lib(monkeypatch, fake_lib)

        props = libcuda.get_device_props(0)

        assert isinstance(props, CudaDeviceProps)
        assert props.name == FAKE_DEVICE_NAME.decode()
        assert props.uuid == FAKE_UUID
        assert props.total_global_mem == FAKE_TOTAL_MEM
        assert props.multiprocessor_count == FAKE_MP_COUNT
        assert props.pci_bus_id == FAKE_PCI_BUS_ID.decode()
        # The uuid must come from the _v2 symbol when it is available.
        assert "cuDeviceGetUuid_v2" in fake_lib.calls
        assert "cuDeviceGetUuid" not in fake_lib.calls

    def test_uuid_falls_back_to_legacy_symbol_when_v2_is_missing(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        fake_lib = FakeCudaLib(missing_symbols=frozenset({"cuDeviceGetUuid_v2"}))
        _install_fake_lib(monkeypatch, fake_lib)

        props = libcuda.get_device_props(0)

        assert props.uuid == FAKE_UUID
        assert "cuDeviceGetUuid" in fake_lib.calls
        assert "cuDeviceGetUuid_v2" not in fake_lib.calls

    def test_uuid_is_none_when_both_symbols_are_missing(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        fake_lib = FakeCudaLib(
            missing_symbols=frozenset({"cuDeviceGetUuid_v2", "cuDeviceGetUuid"}),
        )
        _install_fake_lib(monkeypatch, fake_lib)

        props = libcuda.get_device_props(0)

        assert props.uuid is None
        # The rest of the props must still be populated.
        assert props.name == FAKE_DEVICE_NAME.decode()
        assert props.total_global_mem == FAKE_TOTAL_MEM

    def test_nonzero_return_code_raises_library_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        fake_lib = FakeCudaLib(error_rcs={"cuDeviceGetName": 999})
        _install_fake_lib(monkeypatch, fake_lib)

        with pytest.raises(LibraryError) as exc_info:
            libcuda.get_device_props(0)

        assert exc_info.value.lib == "CUDA"
        assert exc_info.value.func == "cuDeviceGetName"
        assert exc_info.value.code == 999


class TestGetVersion:
    """Tests for libcuda.get_version."""

    def test_decodes_driver_version_without_calling_cuinit(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # cuInit failing must not matter: cuDriverGetVersion is callable
        # before initialization (e.g., on GPU-less hosts).
        fake_lib = FakeCudaLib(error_rcs={"cuInit": 100})
        _install_fake_lib(monkeypatch, fake_lib)

        version = libcuda.get_version()

        assert version == (12, 4)
        assert "cuInit" not in fake_lib.calls


class TestEnsureInit:
    """Tests for libcuda.ensure_init."""

    def test_cuinit_failure_is_sticky(self, monkeypatch: pytest.MonkeyPatch) -> None:
        fake_lib = FakeCudaLib(error_rcs={"cuInit": 100})
        _install_fake_lib(monkeypatch, fake_lib)

        with pytest.raises(LibraryError) as first:
            libcuda.ensure_init()
        with pytest.raises(LibraryError) as second:
            libcuda.ensure_init()

        # The cached error object is re-raised as-is, and the broken driver
        # is not hammered with repeated cuInit calls.
        assert second.value is first.value
        assert first.value.func == "cuInit"
        assert first.value.code == 100
        assert fake_lib.calls.count("cuInit") == 1

    def test_successful_init_is_cached(self, monkeypatch: pytest.MonkeyPatch) -> None:
        fake_lib = FakeCudaLib()
        _install_fake_lib(monkeypatch, fake_lib)

        libcuda.ensure_init()
        libcuda.ensure_init()

        assert fake_lib.calls.count("cuInit") == 1
