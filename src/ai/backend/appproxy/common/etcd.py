from typing import Any

from ai.backend.common.etcd import AsyncEtcd


class TraefikEtcd(AsyncEtcd):
    def _mangle_key(self, k: str) -> str:
        if k.startswith("/"):
            k = k[1:]
        return f"{self.ns}/{k}"

    def _demangle_key(self, k: bytes | str) -> str:
        if isinstance(k, bytes):
            k = k.decode(self.encoding)
        prefix = f"{self.ns}/"
        if k.startswith(prefix):
            k = k[len(prefix) :]
        return k


def convert_to_etcd_dict(item: Any) -> dict:
    def _convert(obj: Any) -> Any:
        if isinstance(obj, list):
            return {str(idx): item for idx, item in enumerate(obj)}
        elif isinstance(obj, dict):
            return {k: _convert(v) for k, v in obj.items()}
        else:
            return obj

    return _convert(item)
