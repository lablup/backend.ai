#!/usr/bin/env python3
"""Regenerate the vendored containerd gRPC stubs in `_grpcapi/`; run only to refresh them.

Inputs: the Go module cache at containerd `CONTAINERD_TAG` and gogo/protobuf, or the
CONTAINERD_PROTO_DIR / GOGO_PROTO_DIR overrides. The hand-written `*.pyi` files are kept.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Provisional: the reference script was unpinned, so the stubs' source tag is unknown.
CONTAINERD_TAG = "v1.7.27"
CONTAINERD_MODULE = f"github.com/containerd/containerd@{CONTAINERD_TAG}"
GOGO_VERSION_GLOB = "github.com/gogo/protobuf@*"

REPO = Path(__file__).resolve().parents[2]
DEST_PKG = "ai.backend.agent.containerd._grpcapi"
DEST_DIR = REPO / "src/ai/backend/agent/containerd/_grpcapi"
PKG_PATH = DEST_PKG.replace(".", "/")

# protoc follows imports, so only the service entry points are listed.
SERVICES = ["containers", "tasks", "images", "snapshots", "content"]


def _find_go_mod(glob: str) -> Path:
    root = Path(os.environ.get("GOPATH", Path.home() / "go")) / "pkg/mod"
    hits = sorted(root.glob(glob))
    if not hits:
        raise SystemExit(f"could not locate proto source for {glob} under {root}")
    return hits[-1]


def _rewrite_proto_imports(text: str) -> str:
    # containerd imports use github.com/... paths, which are not importable Python packages.
    text = re.sub(
        r'import(\s+weak)?\s+"github\.com/containerd/containerd/(api|protobuf)/',
        lambda m: f'import{m.group(1) or ""} "{PKG_PATH}/{m.group(2)}/',
        text,
    )
    return text.replace('"gogoproto/gogo.proto"', f'"{PKG_PATH}/gogoproto/gogo.proto"')


def main() -> None:
    cd_proto = Path(
        os.environ.get("CONTAINERD_PROTO_DIR") or _find_go_mod(CONTAINERD_MODULE)
    )
    gogo_proto = Path(os.environ.get("GOGO_PROTO_DIR") or _find_go_mod(GOGO_VERSION_GLOB))
    print(f"containerd protos: {cd_proto}")
    print(f"gogo protos:       {gogo_proto}")

    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp) / "stage"
        pkg_root = stage / PKG_PATH
        for sub in ("api", "protobuf"):
            for src in (cd_proto / sub).rglob("*.proto"):
                dst = pkg_root / sub / src.relative_to(cd_proto / sub)
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text(_rewrite_proto_imports(src.read_text()))
        (pkg_root / "gogoproto").mkdir(parents=True, exist_ok=True)
        (pkg_root / "gogoproto/gogo.proto").write_text(
            _rewrite_proto_imports((gogo_proto / "gogoproto/gogo.proto").read_text())
        )

        targets = [pkg_root / f"api/services/{s}/v1/{s}.proto" for s in SERVICES]
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

        # Keep the hand-written .pyi files across regeneration.
        pyi_keep = {p.relative_to(DEST_DIR): p.read_text() for p in DEST_DIR.rglob("*.pyi")}
        if DEST_DIR.exists():
            shutil.rmtree(DEST_DIR)
        shutil.copytree(out / PKG_PATH, DEST_DIR)
        for rel, text in pyi_keep.items():
            if (DEST_DIR / rel.with_suffix(".py")).exists():
                (DEST_DIR / rel).write_text(text)
        for d in [DEST_DIR, *[p for p in DEST_DIR.rglob("*") if p.is_dir()]]:
            init = d / "__init__.py"
            if not init.exists():
                init.write_text("")
        print(f"generated {len(list(DEST_DIR.rglob('*_pb2*.py')))} modules -> {DEST_DIR}")


if __name__ == "__main__":
    main()
