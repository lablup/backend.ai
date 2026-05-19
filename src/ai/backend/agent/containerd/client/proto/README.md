# containerd native API — vendored protobuf definitions

Protobuf definitions for containerd's **native gRPC API**, used by the
containerd-backend agent's `ContainerdClient`. This is the native API
(Containers / Tasks / Snapshots / Images / Content / Diff / Transfer /
Leases / Namespaces / Events / Version …), **not** the CRI API — the
CRI path (`../../cri/`) is being retired because kubelet reaps any CRI
sandbox not backed by an API Pod.

## Source

- Upstream: <https://github.com/containerd/containerd>, the `api/` tree
- Tag pinned: `v2.2.0`
- The whole `api/**/*.proto` set is vendored here under `containerd/`.

## Modifications applied at vendoring time

Upstream protos import each other by Go module path, e.g.
`import "github.com/containerd/containerd/api/types/mount.proto";`.
The `github.com` segment is not a valid Python package name, so at
vendoring time every import path **and** the file layout are rewritten:

```
github.com/containerd/containerd/api/   ->   containerd/
```

`api/types/mount.proto` is therefore vendored at
`containerd/types/mount.proto`, and imports referencing it become
`import "containerd/types/mount.proto";`.

### google/rpc/status.proto

`containerd/services/introspection/v1/introspection.proto` imports
`google/rpc/status.proto`. That file is vendored here (`google/rpc/`)
**only so protoc can resolve the import at compile time** — it is
deliberately NOT passed to the code generator. The generated
`introspection_pb2.py` keeps an absolute `from google.rpc import
status_pb2`, which resolves to the `googleapis-common-protos` module
already in the runtime. Generating our own copy would register
`google/rpc/status.proto` in the protobuf descriptor pool a second time
and crash at import. The `google/protobuf/*` well-known types are
handled the same way (provided by protoc / the protobuf runtime).

## Generated stubs

`*_pb2.py`, `*_pb2.pyi`, `*_pb2_grpc.py`, `*_pb2_grpc.pyi` live under
`../generated/` and are committed. Cross-imports are rewritten to be
package-relative so the tree is importable as
`ai.backend.agent.containerd.client.generated.containerd.*`.

## Regeneration

Two codegen venvs are required: `protoletariat` (the import relativizer)
pins `protobuf<6`, while `grpcio-tools` needs `protobuf>=6` — they cannot
share one venv.

```sh
# venv A: protoc + python/mypy plugins (protobuf 6, matches the runtime)
python3 -m venv /tmp/protoc-venv
/tmp/protoc-venv/bin/pip install grpcio-tools mypy-protobuf

# venv B: protoletariat (rewrites generated imports to package-relative)
python3 -m venv /tmp/protol-venv
/tmp/protol-venv/bin/pip install protoletariat

cd src/ai/backend/agent/containerd/client/proto
GEN="$(pwd)/../generated"
rm -rf "$GEN"; mkdir -p "$GEN"

# generate — google/rpc/status.proto stays resolvable via proto_path but
# is intentionally excluded from the file list, so no stub is emitted.
PATH="/tmp/protoc-venv/bin:$PATH" /tmp/protoc-venv/bin/python -m grpc_tools.protoc \
    --proto_path=. \
    --python_out="$GEN" --grpc_python_out="$GEN" \
    --mypy_out="$GEN" --mypy_grpc_out="$GEN" \
    --descriptor_set_out=/tmp/cd.desc --include_imports \
    $(find containerd -name '*.proto' | sort)

# rewrite absolute imports -> package-relative; keep google/* absolute
/tmp/protol-venv/bin/protol --in-place --python-out "$GEN" \
    --exclude-imports-glob 'google/*' raw /tmp/cd.desc

# package markers
find "$GEN" -type d -exec touch {}/__init__.py \;
```
