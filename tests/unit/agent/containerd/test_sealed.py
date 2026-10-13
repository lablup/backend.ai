from __future__ import annotations

import stat
from pathlib import Path
from typing import Any, cast

import pytest

from ai.backend.agent.containerd.sealed import spec_jws_mount, spec_signature, write_spec_jws
from ai.backend.agent.errors.containerd import SealedSpecMissing
from ai.backend.common.types import KernelCreationConfig


def _config(base: KernelCreationConfig, **extra: Any) -> KernelCreationConfig:
    return cast(KernelCreationConfig, {**base, **extra})


class TestSpecSignature:
    def test_no_confidential_key_is_unsealed(self, kernel_config: KernelCreationConfig) -> None:
        assert spec_signature(kernel_config) is None

    def test_none_confidential_is_unsealed(self, kernel_config: KernelCreationConfig) -> None:
        assert spec_signature(_config(kernel_config, confidential=None)) is None

    def test_signature_is_returned(self, kernel_config: KernelCreationConfig) -> None:
        config = _config(kernel_config, confidential={"signature": "aaa.bbb.ccc"})

        assert spec_signature(config) == "aaa.bbb.ccc"

    @pytest.mark.parametrize(
        "confidential",
        [
            {},
            {"signature": None},
            {"signature": ""},
            {"signature": 7},
            {"signature": b"a.b.c"},
            {"signature": "a.b.c\u00e9"},
        ],
        ids=["absent", "none", "empty", "int", "bytes", "non-ascii"],
    )
    def test_sealed_without_a_usable_signature_is_refused(
        self, kernel_config: KernelCreationConfig, confidential: dict[str, Any]
    ) -> None:
        with pytest.raises(SealedSpecMissing):
            spec_signature(_config(kernel_config, confidential=confidential))


class TestWriteSpecJws:
    def test_exact_bytes_and_read_only_mode(self, tmp_path: Path) -> None:
        path = tmp_path / "spec.jws"

        write_spec_jws(path, "aaa.bbb.ccc")

        assert path.read_bytes() == b"aaa.bbb.ccc"
        assert stat.S_IMODE(path.stat().st_mode) == 0o444


class TestSpecJwsMount:
    def test_exact_entry(self, tmp_path: Path) -> None:
        assert spec_jws_mount(tmp_path / "spec.jws") == {
            "destination": "/run/bai/spec.jws",
            "type": "bind",
            "source": str(tmp_path / "spec.jws"),
            "options": ["rbind", "ro", "rprivate"],
        }
