from __future__ import annotations

from ai.backend.agent.containerd._grpcapi.pkg.runtimeoptions.v1 import api_pb2
from ai.backend.agent.containerd.profile.runtime_options import kata_config_path_options


def test_kata_config_path_round_trips() -> None:
    path = "/opt/kata/share/defaults/kata-containers/configuration-qemu-tdx.toml"

    options = kata_config_path_options(path)

    parsed = api_pb2.Options.FromString(options.value)
    assert options.type_url == "runtimeoptions.v1.Options"
    assert parsed.config_path == path
    assert parsed.config_body == b""
