"""Dynamic protoc module; attributes are Any (see scripts/codegen/gen_containerd_api.py)."""

from typing import Any

def __getattr__(name: str) -> Any: ...
