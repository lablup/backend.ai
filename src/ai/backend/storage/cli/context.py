from typing import Any


class CLIContext:
    def __init__(self) -> None:
        self.data: dict[str, Any] = {}
