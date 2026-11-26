# Backend.AI

Backend.AI is a streamlined, container-based computing cluster platform
that hosts popular computing and machine learning frameworks and diverse programming languages,
with pluggable heterogeneous accelerator support.

The `v2` branch is where the manager (including the Sokovan scheduler), agent and storage proxy are
rewritten in Go. The released Python version is on the `main` branch. See
[BEP-1083](proposals/BEP-1083-v2-development.md) for the branch rules and the transition.

## Requirements

| Tool | Version | Used for |
|---|---|---|
| Go | the `go` directive of `go.mod` | Build, code generation, lint and tests |
| Docker with Compose v2 | | The local services |
| PostgreSQL | 17 in CI | Database tests |

## Getting Started

```bash
git clone --branch v2 https://github.com/lablup/backend.ai.git
cd backend.ai
git config core.hooksPath scripts
go build ./...
```

[`scripts/README.md`](scripts/README.md#installing-the-git-hook) lists the other way to install the git hook.

### Local services

```bash
docker compose -f docker-compose.halfstack-main.yml up -d --wait
```

| Services | Compose profile | Host ports |
|---|---|---|
| PostgreSQL, Valkey, etcd, Prometheus | none (always started) | 8100, 8110, 8120, 9090 |
| OpenTelemetry Collector, Loki | `telemetry`, `observability` | 4317, 4318, 3100 |
| Grafana, Grafana MCP, Pyroscope, Tempo, the Postgres, Valkey and node exporters | `observability` | 3000, 3001, 4040, 9187, 9121, 9100 |

The PostgreSQL password is `develove`, and so is the Grafana password of the user `backend`.

### Commands

| Command | Does |
|---|---|
| `go generate ./...` | Generates code |
| `go tool golangci-lint fmt` | Formats |
| `go tool golangci-lint run` | Lints |
| `go test -short ./...` | Runs the tests that need no database |
| `TEST_DATABASE_URL=postgres://postgres:develove@127.0.0.1:8100/backend?sslmode=disable go test ./...` | Runs all tests |
| `INTEGRATION_ENDPOINT=<address> go test -tags integration -count=1 ./tests/integration/...` | Runs the integration tests against a live server |
| `go run ./tools/changelog check` | Checks the [changelog fragments](changes/README.md) |
| `go run ./tools/doclint check --base origin/v2` | Checks the changed documents |
| `go run ./tools/knowledge search <term>` | Searches the `KNOWLEDGE.md` documents |

## Contents in This Repository

| Path | Content |
|---|---|
| `cmd/` | Executables |
| `internal/` | Packages private to the module |
| `api/` | API definitions; `api/legacy/` holds the GraphQL and REST contracts of the Python version |
| `migrations/` | Database migrations |
| `seeds/` | Seed data |
| `tests/` | Integration tests |
| `tools/` | Repository tools: `changelog`, `cvewatch`, `doclint`, `knowledge` |
| `scripts/` | The git hook and other scripts, indexed in [`scripts/README.md`](scripts/README.md) |
| `configs/` | Configurations of the local observability services |
| `changes/` | Changelog fragments |
| `CHANGELOG.md`, `CHANGELOG/` | Release notes |
| `proposals/` | [Backend.AI Enhancement Proposals](proposals/README.md) |
| `glossary/`, `doclint.yaml` | The rules of the document checks |
| `docker-compose.halfstack-main.yml` | The local services |
| `go.mod` | The module `github.com/lablup/backend.ai` and the tool versions |
| `AGENTS.md` | The steering guide for agent-assisted development (`CLAUDE.md` is a symlink to it) |

## Development

See [CONTRIBUTING.md](.github/CONTRIBUTING.md) for the contribution guidelines.

## License

See the [LICENSE file](LICENSE).
