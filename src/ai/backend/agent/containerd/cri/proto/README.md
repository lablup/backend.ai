# CRI Protobuf Definitions

The `api.proto` file in this directory is vendored from
[kubernetes/cri-api](https://github.com/kubernetes/cri-api) (Apache 2.0
License — original copyright header preserved at the top of the file).

## Source

- Upstream: `pkg/apis/runtime/v1/api.proto`
- Branch / tag pinned in this vendoring: `release-1.30`
- Upstream URL: <https://raw.githubusercontent.com/kubernetes/cri-api/release-1.30/pkg/apis/runtime/v1/api.proto>

## Modifications applied at vendoring time

The upstream `api.proto` uses [gogoproto](https://github.com/gogo/protobuf)
extensions for Go-specific code generation hints. These options are
**not understood by the standard `protoc` / `grpc_tools.protoc` Python
compiler** and would cause generation to fail.

The wire format is unaffected by removing them — they only influence
generated Go code. The stripping done at vendoring time:

```
sed -E '/import "github\.com\/gogo\/protobuf\/gogoproto\/gogo\.proto";/d; /^option \(gogoproto\./d' upstream.proto > api.proto
```

This removes the `gogoproto` import and all 7 `option (gogoproto.*)` lines.

## Regeneration

Generated stubs (`api_pb2.py`, `api_pb2.pyi`, `api_pb2_grpc.py`,
`api_pb2_grpc.pyi`) live in `../generated/` and are committed to the
repository. Regenerate when upgrading the proto:

```sh
# Install codegen tools (one-time, not project deps).
# mypy-protobuf provides protoc-gen-mypy + protoc-gen-mypy_grpc which
# emit .pyi stubs for both message and gRPC service code.
pip install --user grpcio-tools mypy-protobuf

# protoc-gen-mypy / protoc-gen-mypy_grpc must be on PATH.
export PATH="$(python3 -m site --user-base)/bin:$PATH"

cd src/ai/backend/agent/containerd/cri
python3 -m grpc_tools.protoc \
    --proto_path=proto \
    --python_out=generated \
    --grpc_python_out=generated \
    --mypy_out=generated \
    --mypy_grpc_out=generated \
    proto/api.proto

# Fix the absolute imports in the gRPC stub + its .pyi (protoc emits
# a top-level `import api_pb2`, which is wrong when the file is loaded
# as part of the `agent.containerd.cri.generated` package).
sed -i '' 's/^import api_pb2 as api__pb2$/from . import api_pb2 as api__pb2/' \
    generated/api_pb2_grpc.py
sed -i '' 's/^import api_pb2 as _api_pb2$/from . import api_pb2 as _api_pb2/' \
    generated/api_pb2_grpc.pyi
```

## Future migration to pants codegen

This vendor-and-commit workflow was chosen for the prototype because
the codebase did not previously use `protoc`-style codegen, and adding
the `pants.backend.codegen.protobuf.python` backend was out of scope.
If multiple components end up needing protobuf codegen, the right move
is to enable that backend and let pants regenerate stubs at build time
from the checked-in `.proto` files.
