# visibility-checker

Checks first-party Python import reachability under `src/ai/backend` against the
repo's `visibility_private_component()` BUILD-file rules.

## Running via Pants

`pants lint ::` invokes the checker automatically. The Pants plugin selects the
appropriate prebuilt binary from `bin/` for the current platform.

## Manual usage

Prebuilt binaries live in `bin/` (tracked with Git LFS):

```bash
# Linux x86-64
./tools/visibility-checker/bin/visibility-checker-linux-x86_64 check

# Linux aarch64
./tools/visibility-checker/bin/visibility-checker-linux-aarch64 check

# macOS Apple Silicon
./tools/visibility-checker/bin/visibility-checker-macos-aarch64 check
```

Useful options:

```bash
# Only check direct import edges, matching Pants' built-in visibility lint shape.
./tools/visibility-checker/bin/visibility-checker-linux-x86_64 check --direct-only

# Print summary information without per-violation details.
./tools/visibility-checker/bin/visibility-checker-linux-x86_64 check --quiet
```

## Updating the prebuilt binaries

Install [`cargo-zigbuild`](https://github.com/rust-cross/cargo-zigbuild) and
[Zig](https://ziglang.org/), then run from this directory:

```bash
cargo zigbuild --release --target x86_64-unknown-linux-musl
cargo zigbuild --release --target aarch64-unknown-linux-musl
cargo zigbuild --release --target aarch64-apple-darwin

cp target/x86_64-unknown-linux-musl/release/visibility-checker bin/visibility-checker-linux-x86_64
cp target/aarch64-unknown-linux-musl/release/visibility-checker  bin/visibility-checker-linux-aarch64
cp target/aarch64-apple-darwin/release/visibility-checker        bin/visibility-checker-macos-aarch64
```

Then commit the updated binaries (they are stored in Git LFS).

## Implementation notes

The checker reads the existing BUILD macro configuration instead of introducing
another config file. It understands the repo's
`visibility_private_component(allowed_dependencies=..., allowed_dependents=...)`
macro and the target-address glob forms used by that macro.
