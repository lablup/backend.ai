from dataclasses import dataclass
from typing import Optional

import pyroscope


@dataclass
class PyroscopeArgs:
    enabled: bool
    app_name: Optional[str]
    server_address: Optional[str]
    sample_rate: Optional[int]


class Profiler:
    def __init__(self, pyroscope_args: PyroscopeArgs) -> None:
        if pyroscope_args.enabled:
            self._pyroscope = pyroscope.configure(
                app_name=pyroscope_args.app_name,
                server_address=pyroscope_args.server_address,
                sample_rate=pyroscope_args.sample_rate,
            )
