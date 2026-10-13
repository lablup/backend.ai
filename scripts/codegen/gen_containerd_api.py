#!/usr/bin/env python3
"""Regenerate the vendored containerd gRPC stubs in `_grpcapi/`; run only to refresh them.

Input: a containerd checkout at `CONTAINERD_TAG` (CONTAINERD_PROTO_DIR, default: the Go module
cache). Its `vendor/` holds the `api` protos (module v1.8.0). Needs grpcio-tools 1.74.0.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CONTAINERD_TAG = "v1.7.27"
CONTAINERD_MODULE = f"github.com/containerd/containerd@{CONTAINERD_TAG}"
VENDORED_API = "vendor/github.com/containerd/containerd/api"

REPO = Path(__file__).resolve().parents[2]
DEST_PKG = "ai.backend.agent.containerd._grpcapi"
DEST_DIR = REPO / "src/ai/backend/agent/containerd/_grpcapi"
PKG_PATH = DEST_PKG.replace(".", "/")

# Entry points; protoc writes Python only for files it is given, so their imports are added.
SERVICES = ["containers", "tasks", "images", "snapshots", "content"]
# Proto trees copied into the stage (source dir relative to the checkout -> stage dir);
# `pkg/runtimeoptions` is the 1.7 location of runtimeoptions.v1.
PROTO_TREES = {VENDORED_API: "api", "pkg/runtimeoptions": "pkg/runtimeoptions"}
EXTRA_TARGETS = ["pkg/runtimeoptions/v1/api.proto"]
PYI_STUB = '''"""Dynamic protoc module; attributes are Any (see scripts/codegen/gen_containerd_api.py)."""

from typing import Any

def __getattr__(name: str) -> Any: ...
'''


def _find_go_mod(glob: str) -> Path:
    root = Path(os.environ.get("GOPATH", Path.home() / "go")) / "pkg/mod"
    hits = sorted(root.glob(glob))
    if not hits:
        raise SystemExit(f"could not locate proto source for {glob} under {root}")
    return hits[-1]


def _rewrite_proto_imports(text: str) -> str:
    # containerd imports use github.com/... paths, which are not importable Python packages.
    return re.sub(
        r'import(\s+weak)?\s+"github\.com/containerd/containerd/(api|protobuf)/',
        lambda m: f'import{m.group(1) or ""} "{PKG_PATH}/{m.group(2)}/',
        text,
    )


def _import_closure(stage: Path, roots: list[Path]) -> list[Path]:
    seen: dict[Path, None] = {}
    todo = list(roots)
    while todo:
        proto = todo.pop()
        if proto in seen:
            continue
        seen[proto] = None
        for imported in re.findall(r'^import\s+(?:weak\s+)?"([^"]+)";', proto.read_text(), re.M):
            if (stage / imported).exists():
                todo.append(stage / imported)
    return sorted(seen)


def main() -> None:
    cd_proto = Path(os.environ.get("CONTAINERD_PROTO_DIR") or _find_go_mod(CONTAINERD_MODULE))
    print(f"containerd protos: {cd_proto}")

    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp) / "stage"
        pkg_root = stage / PKG_PATH
        for sub, dest in PROTO_TREES.items():
            for src in (cd_proto / sub).rglob("*.proto"):
                dst = pkg_root / dest / src.relative_to(cd_proto / sub)
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text(_rewrite_proto_imports(src.read_text()))

        targets = [pkg_root / f"api/services/{s}/v1/{s}.proto" for s in SERVICES]
        targets += [pkg_root / t for t in EXTRA_TARGETS]
        targets = _import_closure(stage, targets)
        out = Path(tmp) / "out"
        out.mkdir()
        cmd = [
            sys.executable, "-m", "grpc_tools.protoc",
            f"-I{stage}",
            f"--python_out={out}",
            f"--grpc_python_out={out}",
            *[str(t) for t in targets],
        ]  # fmt: skip
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(res.stderr, file=sys.stderr)
            raise SystemExit("protoc failed")

        if DEST_DIR.exists():
            shutil.rmtree(DEST_DIR)
        shutil.copytree(out / PKG_PATH, DEST_DIR)
        for grpc_module in DEST_DIR.rglob("*_pb2_grpc.py"):
            if "Servicer(" not in grpc_module.read_text():  # message-only proto
                grpc_module.unlink()
        for module in DEST_DIR.rglob("*_pb2*.py"):
            module.with_suffix(".pyi").write_text(PYI_STUB)
        for d in [DEST_DIR, *[p for p in DEST_DIR.rglob("*") if p.is_dir()]]:
            init = d / "__init__.py"
            if not init.exists():
                init.write_text("")
        print(f"generated {len(list(DEST_DIR.rglob('*_pb2*.py')))} modules -> {DEST_DIR}")


if __name__ == "__main__":
    main()
