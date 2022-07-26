from typing import Dict, Final, Optional, Tuple

from ai.backend.common.distributed.raft.utils import AtomicInteger


class RespInterpreter:
    def __init__(self):
        self._supported_commands: Final[Tuple[str, ...]] = ["INCRBY", "INCR", "GET", "SET"]
        self._dict: Dict[str, AtomicInteger] = {}

    def execute(self, command: str) -> Optional[int]:
        command, *args = command.split()
        assert command in self._supported_commands, f'command "{command}" is not supported.'
        match command:
            case "INCRBY":
                assert (
                    len(args) >= 2
                ), "Not enough arguments are provided. (Required: INCRBY <key> <value>)"
                key, value, *_ = args
                self._dict[key] = self._dict.get(key, AtomicInteger(0)).increase(int(value))
            case "INCR":
                assert len(args) >= 1, "Not enough arguments are provided. (Required: INCR <key>)"
                key, *_ = args
                self._dict[key] = self._dict.get(key, AtomicInteger(0)).increase()
            case "GET":
                assert len(args) >= 1, "Not enough arguments are provided. (Required: GET <key>)"
                key, *_ = args
                if atomic_value := self._dict.get(key):
                    return atomic_value.value
            case "SET":
                assert (
                    len(args) >= 2
                ), "Not enough arguments are provided. (Required: SET <key> <value>)"
                key, value, *_ = args
                try:
                    self._dict[key] = AtomicInteger(int(value))
                except ValueError:
                    pass
        return None
