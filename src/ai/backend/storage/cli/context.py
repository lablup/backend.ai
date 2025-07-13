from typing import Any

import click


class CLIContext:
    def __init__(self) -> None:
        self.data: dict[str, Any] = {}