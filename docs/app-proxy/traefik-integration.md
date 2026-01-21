# Traefik Integration
Traefik can be used as a proxy dataplane for AppProxy worker. When enabled, AppProxy Worker operates in a "trimmed down" mode, with certain features like Redis Event Bus and Proxy dataplanes disabled on startup.

## What's supported
- HTTP: All
- TCP: Without last used time marker

## Installing traefik
1. Download traefik binary from [traefik release page](https://github.com/traefik/traefik/releases).
2. Extract [AppProxy's traefik plugin](https://github.com/lablup/backend.ai-appproxy-worker-traefik) next to the traefik binary. After completed, the folder structure should look like:
```bash
.
├── traefik.yml
├── plugins-local
│   └── src
│       └── backend.ai
│           ├── appproxy-traefik-plugin
│           │   └── plugin.wasm
│           └── appproxy-traefik-plugin-go
│               ├── go.mod
│               ├── go.sum
│               └── plugin.go
└── traefik
```

## Writing down traefik configuration file
## Common
```yaml
entrypoints:
  traefik:
    address: 127.0.0.1:8080
api:
  insecure: true
providers:
  etcd:
    rootKey: "traefik/worker_<worker authority>"
    endpoints:
    - 127.0.0.1:8121
experimental:
  localPlugins:
    appproxy-traefik-plugin:
      moduleName: backend.ai/appproxy-traefik-plugin
      settings:
        mounts:
        - "/home/ubuntu/appproxy:/appproxy-traefik"
    appproxy-traefik-plugin-go:
      moduleName: backend.ai/appproxy-traefik-plugin-go
```
- Define an entrypoint named `traefik`. This will act as an entrypoint to Traefik API server, which later will be accessed from AppProxy worker, so it is best to leave the host as loopback (`127.0.0.1`) for security measures.
- Mention about every Etcd endpoints under `providers.etcd.endpoints`.
- Set `providers.etcd.rootKey` to `traefik/worker_` combined with target worker's authority (e.g. `traefik/worker_worker-1`).
- `experimental` directive should include plugin definition to AppProxy's Traefik plugin. Use the example configuration posted above as a baseline, and modify the left side of the `mounts` config as the folder where `traefik` binary will be located.

### Port Proxy
```yaml
entryPoints:
  portproxy_10205:
    address: 0.0.0.0:10205
  portproxy_10206:
    address: 0.0.0.0:10206
  portproxy_10207:
    address: 0.0.0.0:10207
  portproxy_10208:
    address: 0.0.0.0:10208
  portproxy_10209:
    address: 0.0.0.0:10209
```

- `entryPoints` config should contain a definition of every HTTP/TCP ports to be exposed, with each entrypoint named as `portproxy_<port number>`.
    - <port number> should be the number user connects to.

### Wildcard Domain Proxy
```yaml
entryPoints:
    domainproxy:
        address: 0.0.0.0:8443
```

- `entryPoints` config should contain one entrypoint named as `domainproxy`.

### Complete examples
```yaml
# Port Proxy
entryPoints:
  portproxy_10205:
    address: 0.0.0.0:10205
  portproxy_10206:
    address: 0.0.0.0:10206
  portproxy_10207:
    address: 0.0.0.0:10207
  portproxy_10208:
    address: 0.0.0.0:10208
  portproxy_10209:
    address: 0.0.0.0:10209
  traefik:
    address: 127.0.0.1:8080
api:
  insecure: true
providers:
  etcd:
    rootKey: "traefik/worker_<worker authority>"
    endpoints:
    - 127.0.0.1:8121
experimental:
  localPlugins:
    appproxy-traefik-plugin:
      moduleName: backend.ai/appproxy-traefik-plugin
      settings:
        mounts:
        - "/home/ubuntu/appproxy:/appproxy-traefik"
    appproxy-traefik-plugin-go:
      moduleName: backend.ai/appproxy-traefik-plugin-go
```
```yaml
# Wildcard Proxy
entryPoints:
  domainproxy:
    address: 0.0.0.0:8443
  traefik:
    address: 127.0.0.1:8080
api:
  insecure: true
providers:
  etcd:
    rootKey: "traefik/worker_<worker authority>"
    endpoints:
    - 127.0.0.1:8121
experimental:
  localPlugins:
    appproxy-traefik-plugin:
      moduleName: backend.ai/appproxy-traefik-plugin
      settings:
        mounts:
        - "/home/ubuntu/appproxy:/appproxy-traefik"
    appproxy-traefik-plugin-go:
      moduleName: backend.ai/appproxy-traefik-plugin-go
```

## Migrating AppProxy configuration

### Path relocations

| Old Configuration Path | New Configuration Path | Notes |
|------------------------|------------------------|-------|
| `[proxy_worker].frontend_mode` | `[proxy_worker].frontend_mode` | Should be set to `traefik` |
| _(new)_ | `[proxy_worker.traefik].frontend_mode` | Move existing value (`port` or `wildcard`) here |

#### Port mode specific changes

| Old Configuration Path | New Configuration Path | Notes |
|------------------------|------------------------|-------|
| `[proxy_worker.port_proxy]` | `[proxy_worker.traefik.port_proxy]` | Move the entire section |
| `.host`<br>`.advertised_host` | `.advertised_host` | Merged into single config.<br>• Same network: use node's IP address<br>• Behind proxy/NAT: use the proxy hostname |
| `.bind_port_range`<br>`.advertised_port_range` | `.port_range` | Merged into single config.<br>Apply same networking rules as advertised_host |

#### Wildcard mode specific changes

| Old Configuration Path | New Configuration Path | Notes |
|------------------------|------------------------|-------|
| `[proxy_worker.wildcard_domain]` | `[proxy_worker.traefik.wildcard_domain]` | Move the entire section |
| `.bind_addr.host` | _(removed)_ | No longer required |
| `.bind_addr.port`<br>`.advertised_port` | `.advertised_port` | Merged into single config.<br>• Same network: use traefik listening port<br>• Behind proxy/NAT: use public port number |

### New configurations

| Configuration Path | Description |
|-------------------|-------------|
| `[proxy_coordinator].enable_traefik` | Must be set to `true` |
| `[proxy_coordinator.traefik].etcd` | etcd configuration (identical schema to Backend.AI Core), but namespace should be set to `traefik` |
| `[proxy_worker.traefik].api_port` | Port number of the `traefik` entrypoint |
| `[proxy_worker.traefik].etcd` | etcd configuration (identical schema to Backend.AI Core), but namespace should be set to `traefik` |
| `[proxy_worker.traefik].last_used_time_marker_directory` | Directory where `traefik` binary is located (for named pipe communication) |

## Considerations for High-Availability setup
As traefik does not care about its own HA/Cluster feature, Worker HA setup will be pretty much the same without Traefik.
- Along with worker packages, traefik should also be deployed at every worker nodes.
- Use every other configurations (HAProxy, keepalived, proxy-worker.toml) as is.
