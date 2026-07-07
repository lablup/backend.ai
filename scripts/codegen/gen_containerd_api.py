#!/usr/bin/env python3
"""Generate Python gRPC stubs for the native containerd API (BEP-1055).

containerd's .proto files use fully-qualified `github.com/containerd/containerd/...`
import paths, which protoc turns into invalid Python imports (`github.com` is not an
importable package). We work around this by *rewriting* the proto imports to the target
Python package path BEFORE running protoc, so the generated modules import each other
with valid, fully-qualified names rooted at the destination package.

Sources are taken from the Go module cache (containerd + gogo/protobuf are pulled in as
build deps); override with CONTAINERD_PROTO_DIR / GOGO_PROTO_DIR if needed.

Usage:  ./py scripts/codegen/gen_containerd_api.py
Output: src/ai/backend/agent/containerd/_grpcapi/
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEST_PKG = "ai.backend.agent.containerd._grpcapi"
DEST_DIR = REPO / "src/ai/backend/agent/containerd/_grpcapi"
PKG_PATH = DEST_PKG.replace(".", "/")  # ai/backend/agent/containerd/_grpcapi

# Services we need (+ their transitive api/types & protobuf deps are pulled in wholesale).
SERVICES = ["containers", "tasks", "images", "snapshots", "content"]


def _find_go_mod(*globs: str) -> Path:
    roots = [Path(os.environ.get("GOPATH", Path.home() / "go")) / "pkg/mod"]
    for root in roots:
        for g in globs:
            hits = sorted(root.glob(g))
            if hits:
                return hits[-1]  # newest
    raise SystemExit(f"could not locate proto source for {globs} under {roots}")


def _rewrite_proto_imports(text: str) -> str:
    # github.com/containerd/containerd/{api,protobuf}/... -> <pkg>/{api,protobuf}/...
    text = re.sub(
        r'import(\s+weak)?\s+"github\.com/containerd/containerd/(api|protobuf)/',
        lambda m: f'import{m.group(1) or ""} "{PKG_PATH}/{m.group(2)}/',
        text,
    )
    # gogoproto/gogo.proto -> <pkg>/gogoproto/gogo.proto
    text = text.replace('"gogoproto/gogo.proto"', f'"{PKG_PATH}/gogoproto/gogo.proto"')
    return text


def main() -> None:
    cd_proto = Path(
        os.environ.get("CONTAINERD_PROTO_DIR")
        or _find_go_mod("github.com/containerd/containerd@*")
    )
    gogo_proto = Path(
        os.environ.get("GOGO_PROTO_DIR") or _find_go_mod("github.com/gogo/protobuf@*")
    )
    print(f"containerd protos: {cd_proto}")
    print(f"gogo protos:       {gogo_proto}")

    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp) / "stage"
        pkg_root = stage / PKG_PATH
        (pkg_root).mkdir(parents=True)
        # Copy api/ + protobuf/ under the destination package path, rewriting imports.
        for sub in ("api", "protobuf"):
            for src in (cd_proto / sub).rglob("*.proto"):
                rel = src.relative_to(cd_proto / sub)
                dst = pkg_root / sub / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text(_rewrite_proto_imports(src.read_text()))
        (pkg_root / "gogoproto").mkdir(parents=True, exist_ok=True)
        (pkg_root / "gogoproto/gogo.proto").write_text(
            _rewrite_proto_imports((gogo_proto / "gogoproto/gogo.proto").read_text())
        )

        # Compile: all api/types + protobuf + gogoproto (deps) + the target services.
        # (Skip introspection/diff/events/version — they pull in google/rpc which is
        # not bundled and which we do not need.)
        targets = [
            *(pkg_root / "api/types").rglob("*.proto"),
            *(pkg_root / "protobuf").rglob("*.proto"),
            pkg_root / "gogoproto/gogo.proto",
            *[pkg_root / f"api/services/{s}/v1/{s}.proto" for s in SERVICES],
        ]
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
        errors = [ln for ln in res.stderr.splitlines() if "warning" not in ln.lower()]
        if res.returncode != 0 or errors:
            print("\n".join(errors) or res.stderr, file=sys.stderr)
            if res.returncode != 0:
                raise SystemExit("protoc failed")

        # Install into the repo, with package __init__.py markers.
        gen_pkg = out / PKG_PATH
        if DEST_DIR.exists():
            shutil.rmtree(DEST_DIR)
        shutil.copytree(gen_pkg, DEST_DIR)
        for d in [DEST_DIR, *[p for p in DEST_DIR.rglob("*") if p.is_dir()]]:
            init = d / "__init__.py"
            if not init.exists():
                init.write_text("")
        n = len(list(DEST_DIR.rglob("*_pb2.py")))
        g = len(list(DEST_DIR.rglob("*_pb2_grpc.py")))
        print(f"generated {n} message modules + {g} service stubs -> {DEST_DIR}")


if __name__ == "__main__":
    main()
