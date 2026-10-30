# AppProxy Traefik Go Plugin

Tracks circuit and session access times and WebSocket activity through the
AppProxy worker's Unix socket API. Authentication remains in the
[Rust/WASM plugin](https://github.com/lablup/backend.ai-appproxy-worker-traefik).
Both plugins are required for AppProxy's
Traefik HTTP routing.

## Development

Run from this directory:

```sh
gofmt -w plugin.go
go vet ./...
go test ./...
```

## Integration

- The coordinator generates the `id`, `sessionids`, and `lastusedmarkerpath` settings.
- Traefik loads the source from `plugins-local/src/backend.ai/appproxy-traefik-plugin-go/`.
- This source import does not change CI, packaging, or deployment configuration.

See the [Traefik integration guide](../../docs/app-proxy/traefik-integration.md).
