# visibility-checker

Checks first-party Python import reachability under `src/ai/backend` against the
repo's `visibility_private_component()` BUILD-file rules.

Manual usage:

```bash
cargo run --manifest-path tools/visibility-checker/Cargo.toml -- check
```

Useful options:

```bash
# Only check direct import edges, matching Pants' built-in visibility lint shape.
cargo run --manifest-path tools/visibility-checker/Cargo.toml -- check --direct-only

# Print summary information without per-violation details.
cargo run --manifest-path tools/visibility-checker/Cargo.toml -- check --quiet
```

The checker intentionally reads the existing BUILD macro configuration instead
of introducing another config file. It currently understands this repository's
`visibility_private_component(allowed_dependencies=..., allowed_dependents=...)`
macro and the target-address glob forms used by that macro.
