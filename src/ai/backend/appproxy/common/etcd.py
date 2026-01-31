from typing import Any

from ai.backend.common.etcd import AsyncEtcd


class TraefikEtcd(AsyncEtcd):
    def _mangle_key(self, k: str) -> str:
        k = k.removeprefix("/")
        return f"{self.ns}/{k}"

    def _demangle_key(self, k: bytes | str) -> str:
        if isinstance(k, bytes):
            k = k.decode(self.encoding)
        prefix = f"{self.ns}/"
        return k.removeprefix(prefix)


def convert_to_etcd_dict(item: Any) -> dict[str, Any]:
    def _convert(obj: Any) -> Any:
        if isinstance(obj, list):
            return {str(idx): item for idx, item in enumerate(obj)}
        if isinstance(obj, dict):
            return {k: _convert(v) for k, v in obj.items()}
        return obj

    return _convert(item)
