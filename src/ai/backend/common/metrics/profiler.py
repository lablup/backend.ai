from dataclasses import dataclass

import pyroscope


@dataclass
class PyroscopeArgs:
    enabled: bool
    application_name: str
    server_address: str
    sample_rate: int


class Profiler:
    def __init__(self, pyroscope_args: PyroscopeArgs) -> None:
        if pyroscope_args.enabled:
            pyroscope.configure(
                application_name=pyroscope_args.application_name,
                server_address=pyroscope_args.server_address,
                sample_rate=pyroscope_args.sample_rate,
            )
