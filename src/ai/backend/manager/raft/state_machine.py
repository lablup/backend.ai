from typing import Any, NamedTuple, Optional, Self


class ApplyResult(NamedTuple):
    key: str
    old_value: Optional[str]
    new_value: Optional[str]
    revision: int


class SetCommand:
    key: str
    value: str

    def __init__(self, key: str, value: str) -> None:
        self.key = key
        self.value = value

    def encode(self) -> bytes:
        return f"{self.key}={self.value}".encode("utf-8")

    @classmethod
    def decode(cls, packed: bytes) -> Self:
        unpacked = packed.decode("utf-8").split("=", 1)
        if len(unpacked) != 2:
            raise ValueError("Invalid packed data")
        return cls(unpacked[0], unpacked[1])


class HashStore:
    _store: dict[str, Any]
    _revision: int

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}
        self._revision = 0

    def get(self, key: str) -> Optional[str]:
        return self._store.get(key)

    def as_dict(self) -> dict:
        return self._store

    async def apply(self, msg: bytes) -> Optional[bytes]:
        message = SetCommand.decode(msg)
        # old_value = self._store.get(message.key)
        new_value = message.value

        if new_value == "":
            self._store.pop(message.key, None)
        else:
            self._store[message.key] = new_value

        self._revision += 1

        # apply_res = ApplyResult(
        #     key=message.key,
        #     old_value=old_value,
        #     new_value=new_value,
        #     revision=self._revision,
        # )

        # todo: check this—might needs to pass the apply result up to watchers
        # return json.dumps(apply_res._asdict()).encode("utf-8")
        return msg

    def current_revision(self) -> int:
        return self._revision

    async def snapshot(self) -> bytes:
        return "\n".join(f"{k}={v}" for k, v in self._store.items()).encode("utf-8")

    async def restore(self, snapshot: bytes) -> None:
        self._store = dict(line.split("=", 1) for line in snapshot.decode("utf-8").split("\n"))
        self._revision = 0
