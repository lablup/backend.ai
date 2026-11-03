# Backend.AI

[![PyPI release version](https://badge.fury.io/py/backend.ai-manager.svg)](https://pypi.org/project/backend.ai-manager/)
![Supported Python versions](https://img.shields.io/pypi/pyversions/backend.ai-manager.svg)
![Wheels](https://img.shields.io/pypi/wheel/backend.ai-manager.svg)
[![Gitter](https://badges.gitter.im/lablup/backend.ai.svg)](https://gitter.im/lablup/backend.ai)

Backend.AI is a streamlined, container-based computing cluster platform
that hosts popular computing and machine learning frameworks and diverse programming languages,
with pluggable heterogeneous accelerator support including CUDA GPU, ROCm GPU,
Rebellions, FuriosaAI, HyperAccel, Intel Gaudi, Tenstorrent, Google TPU,
Graphcore IPU and other NPUs.

It allocates and isolates the underlying computing resources for multi-tenant
sessions on demand or in batches, with customizable job schedulers and its own
orchestrator named "Sokovan".

All its functions are exposed as REST and GraphQL APIs.


## Requirements

### Python and Build Tools

- **Python**: 3.13.x (main branch requires CPython 3.13.18)
- **Pants**: 2.27.x
- See [full version compatibility table](src/ai/backend/README.md#development-setup)

### Infrastructure

**Container engine** (one of):

| Engine | Supported | Accelerator requirements |
|---|---|---|
| Docker | 20.10+ | The nvidia runtime registered with the daemon (`nvidia-ctk runtime configure --runtime=docker`) |
| Podman | 5.4.0+ | A CDI spec for the accelerator under `/etc/cdi` or `/var/run/cdi` (`nvidia-ctk cdi generate` for NVIDIA GPUs) |

**Distributions packaging Podman 5.4.0+**:

| OS | Minimum version | Packaged Podman |
|---|---|---|
| RHEL | 9.x | 5.4.0+ (older minors, for example under EUS, may ship older Podman; check the version the OS repo offers) |
| Rocky Linux | 9.6 | 5.4.0 |
| AlmaLinux | 9.6 | 5.4.0 |
| Oracle Linux | 9.6 | 5.4.0 |
| CentOS Stream | 9 | 5.8.5 |
| Ubuntu | 26.04 LTS | 5.7.0 |
| Debian | 13 | 5.4.2 |

- Ubuntu 24.04 LTS packages Podman 4.9.3 and Debian 12 packages 4.3.1, both below the minimum; use Docker there.

**Required**:
- Docker Compose v2
- PostgreSQL 16+ (tested with 16.3)
- Valkey 9.1+ (tested with 9.1.0; Redis-compatible)
- etcd 3.5+ (tested with 3.5.14)
- Prometheus 3.x (tested with 3.1.0)

**Recommended** (for observability):
- Grafana 11.x (tested with 11.4.0)
- Loki 3.x (tested with 3.5.0)
- Tempo 2.x (tested with 2.7.2)
- OpenTelemetry Collector

See [Infrastructure Documentation](src/ai/backend/README.md#infrastructure-layer) for detailed infrastructure setup.

### System

- **OS**: Linux (Debian/RHEL-based) or macOS
- **Permissions**: sudo access for installation
- **Resources**: 4+ CPU cores, 8GB+ RAM recommended for development


## Getting Started

### Quick Start (Development)

#### 1. Clone and Install

```bash
git clone https://github.com/lablup/backend.ai.git
cd backend.ai
./scripts/install-dev.sh
```

The script:
- Checks required dependencies (Docker, Python and others)
- Sets up the Python virtual environment with Pants
- Starts halfstack infrastructure (PostgreSQL, Valkey, etcd, Apollo Router). Only required services start by default; observability and object storage are opt-in through Compose profiles (`--profile observability`, `--profile storage`)
- Initializes database schemas
- Creates default API keypairs and user accounts

#### 2. Start Backend.AI Services

Start each component in a separate terminal:

**Manager** (Terminal 1):
```bash
./backend.ai mgr start-server --debug
```

**Agent** (Terminal 2):
```bash
./backend.ai ag start-server --debug
```

**Storage Proxy** (Terminal 3):
```bash
./backend.ai storage start-server --debug
```

**Webserver** (Terminal 4):
```bash
./backend.ai web start-server --debug
```

**Account Manager** (Terminal 5, optional for SSO and unified user profile):
```bash
./backend.ai am start-server --debug
```

**App Proxy** (Terminal 6-7, optional for in-container service access):
```bash
./backend.ai app-proxy-coordinator start-server --debug
./backend.ai app-proxy-worker start-server --debug
```

#### 3. Run Your First Session

Set up the client environment:
```bash
source env-local-user-session.sh
# This script prints your default User ID and Password;
./backend.ai login
# When prompted, enter the User ID and Password shown above.
```

Run a simple Python session:
```bash
./backend.ai run python -c "print('Hello Backend.AI!')"
```

Alternatively, access the Web UI at **http://localhost:8090** with credentials from the `env-local-*.sh` files.

### Accessing Sessions (also known as Kernels)

Backend.AI provides WebSocket tunneling into individual sessions (containers),
so users can access in-container applications from a browser or the client CLI
directly and securely.

* Jupyter: data scientists' favorite tool
   * Most container images have intrinsic Jupyter and JupyterLab support.
* Web-based terminal
   * All sessions have intrinsic ttyd support.
* SSH
   * All sessions have intrinsic SSH/SFTP/SCP support with an auto-generated per-user SSH keypair.
     PyCharm and other IDEs can use on-demand sessions with SSH remote interpreters.
* VSCode
   * Most sessions have intrinsic web-based VSCode support.

### Working with Storage

Backend.AI provides an abstraction layer over existing network-based storage
(for example, NFS and SMB), called vfolders.
A vfolder works like cloud storage that mounts into any session and is shared
between users and projects with differentiated privileges.

### Installation for Multi-node Tests and Production

See [our documentation](http://docs.backend.ai) for community-supported materials.
Contact the sales team (contact@lablup.com) for professional paid support and deployment options.


## Architecture

For comprehensive system architecture, component interactions and infrastructure details, see:

**[Component Architecture Documentation](src/ai/backend/README.md)**

This document covers:
- System architecture diagrams and component flow
- Port numbers and infrastructure setup
- Component dependencies and communication protocols
- Development and production environment configuration


## Contents in This Repository

This repository contains all open-source server-side components and the Python client SDK
as a reference implementation of API clients.

### Directory Structure

* `src/ai/backend/`: Source code
  - `manager/`: Manager as the cluster control plane
  - `manager/api`: Manager API handlers
  - `account_manager/`: Unified user profile and SSO management
  - `agent/`: Agent as the per-node controller
  - `agent/docker/`: The Agent's Docker backend
  - `agent/kubernetes/`: The Agent's Kubernetes backend
  - `agent/dummy/`: The Agent's dummy backend
  - `kernel/`: The Agent's kernel runner counterpart
  - `runner/`: The Agent's in-kernel prebuilt binaries
  - `helpers/`: The Agent's in-kernel helper package
  - `common/`: Shared utilities
  - `client/`: Client SDK
  - `cli/`: Unified CLI for all components
  - `install/`: SCIE-based TUI installer
  - `storage/`: Storage proxy for offloading storage operations
  - `storage/api`: Storage proxy manager API and storage proxy client API
  - `appproxy/`: App proxy for accessing container apps from outside
  - `appproxy/coordinator`: App proxy coordinator that provisions routing circuits
  - `appproxy/worker`: App proxy worker that forwards traffic
  - `web/`: Web UI server
    - `static/`: Backend.AI WebUI release artifacts
  - `logging/`: Logging subsystem
  - `plugin/`: Plugin subsystem
  - `test/`: Integration test suite
  - `testutils/`: Shared utilities used by unit tests
  - `meta/`: Legacy meta package
  - `accelerator/`: Intrinsic accelerator plugins
* `docs/`: Unified documentation
* `tests/`
  - `manager/`, `agent/`, ...: Per-component unit tests
* `configs/`
  - `manager/`, `agent/`, ...: Per-component sample configurations
* `docker/`: Dockerfiles for auxiliary containers
* `fixtures/`
  - `manager/`, ...: Per-component fixtures for development setup and tests
* `plugins/`: A directory to place plugins such as accelerators and monitors
* `third-party-plugins/`: Backend.AI plugins for third-party software (for example, the App Proxy Traefik Go plugin)
* `scripts/`: Scripts to assist development workflows
  - `install-dev.sh`: The single-node development setup script from the working copy
* `stubs/`: Type annotation stub packages written by us
* `tools/`: A directory to host Pants-related tooling
* `dist/`: A directory to put build artifacts (`.whl` files) and Pants-exported virtualenvs
* `changes/`: Changelog fragments for towncrier
* `pants.toml`: The Pants configuration
* `pyproject.toml`: Tooling configuration (towncrier, pytest, mypy)
* `BUILD`: The root build config file
* `**/BUILD`: Per-directory build config files
* `BUILD_ROOT`: An indicator to mark the build root directory for Pants
* `AGENTS.md`: The steering guide for agent-assisted development (`CLAUDE.md` is a symlink to it)
* `requirements.txt`: The unified requirements file
* `*.lock`, `tools/*.lock`: The dependency lock files
* `docker-compose.*.yml`: Per-version recommended halfstack container configs
* `README.md`: This file
* `MIGRATION.md`: The migration guide for updating between major releases
* `VERSION`: The unified version declaration

Server-side components are licensed under LGPLv3 to promote non-proprietary open
innovation in the open-source community. Other shared libraries and client SDKs
are distributed under the MIT license.

You have no obligation to open your service or system code if you run the
server-side components as they are (for example, run them as daemons or import the components
without modification into your code).
Contact us (contact-at-lablup-com) for commercial consulting and for licensing
details and options about individual use cases.


## Major Components

Backend.AI consists of the following core components:

### Server-Side Components

**[Manager](src/ai/backend/manager/README.md)** - Central API gateway and orchestrator
- Routes REST and GraphQL requests and orchestrates cluster operations
- Session scheduling through the Sokovan orchestrator
- User authentication and RBAC authorization
- Plugin interfaces: `backendai_scheduler_v10`, `backendai_agentselector_v10`, `backendai_hook_v20`, `backendai_webapp_v20`, `backendai_monitor_stats_v10`, `backendai_monitor_error_v10`
- Legacy repo: https://github.com/lablup/backend.ai-manager

**[Account Manager](src/ai/backend/account_manager/README.md)** - Unified user profile and SSO daemon
- Manages user accounts, including the accounts of the Backend.AI first-party service
- Single sign-on across Backend.AI components

**[Agent](src/ai/backend/agent/README.md)** - Kernel lifecycle management on nodes
- Manages Docker containers (kernels) on individual nodes
- Registers itself with the cluster through the agent heartbeat
- Plugin interfaces: `backendai_accelerator_v21`, `backendai_monitor_stats_v10`, `backendai_monitor_error_v10`
- Legacy repo: https://github.com/lablup/backend.ai-agent

**[Storage Proxy](src/ai/backend/storage/README.md)** - Vfolder and storage backend abstraction
- Unified interface for multiple storage backends
- Real-time performance metrics and acceleration APIs
- Legacy repo: https://github.com/lablup/backend.ai-storage-proxy

**[Webserver](src/ai/backend/web/README.md)** - Web UI hosting and session management
- Hosts the Backend.AI WebUI single-page application
- Session management and API request signing
- Legacy repo: https://github.com/lablup/backend.ai-webserver

**Synchronizing the static Backend.AI WebUI version:**
```console
$ scripts/download-webui-release.sh <target version to download>
```

**[App Proxy](src/ai/backend/appproxy/coordinator/README.md)** - Service routing and load balancing
- Routes traffic to in-container services (Jupyter, VSCode and others)
- Dynamic circuit provisioning and health monitoring

### Container Runtime Components

**[Kernels](https://github.com/lablup/backend.ai-kernels)** - Container image recipes
- Dockerfile-based computing environment recipes
- Support for popular machine learning frameworks and programming languages

**[Jail](https://github.com/lablup/backend.ai-jail)** - Programmable sandbox (Rust)
- ptrace-based system call filtering
- Resource control and security enforcement

**[Hook](https://github.com/lablup/backend.ai-hook)** - In-container runtime library
- libc overrides for resource control
- Web-based interactive stdin support

### Client SDK Libraries

The project provides client SDKs in popular programming languages (MIT License):

- **Python** - `pip install backend.ai-client` | [GitHub](src/ai/backend/client) | Includes CLI
- **Java** - [Releases](https://github.com/lablup/backend.ai-client-java)
- **JavaScript** - `npm install backend.ai-client` | [GitHub](https://github.com/lablup/backend.ai-client-js)
- **PHP** - (under preparation) `composer require lablup/backend.ai-client` | [GitHub](https://github.com/lablup/backend.ai-client-php)


## Plugins

Backend.AI supports plugin-based extensibility through Python package entrypoints:

**Accelerator plugins** (`backendai_accelerator_v21`)
- [CUDA](src/ai/backend/accelerator/cuda_open) - NVIDIA GPU support
- [Mock](src/ai/backend/accelerator/mock) - A mock accelerator for development without actual GPUs
- [ROCm](src/ai/backend/accelerator/rocm) - AMD GPU support
- [Furiosa](src/ai/backend/accelerator/furiosa) - Furiosa NPU (Warboy / RNGD) support
- [Habana](src/ai/backend/accelerator/habana) - Intel Gaudi HPU (Gaudi 2, Gaudi 3) support
- [Hyperaccel](src/ai/backend/accelerator/hyperaccel) - Hyperaccel LPU support
- [IPU](src/ai/backend/accelerator/ipu) - Graphcore IPU support
- [Rebellions](src/ai/backend/accelerator/rebellions) - Rebellions NPU (ATOM, ATOM+, ATOM Max) support
- [Tenstorrent](src/ai/backend/accelerator/tenstorrent) - Tenstorrent NPU (Wormhole, Blackhole) support
- [TPU](src/ai/backend/accelerator/tpu) - Google TPU (v2 and newer generations) support

**Monitoring plugins**
- [`backendai_monitor_stats_v10`](https://github.com/lablup/backend.ai-monitor-datadog) - Datadog statistics collector
- [`backendai_monitor_error_v10`](https://github.com/lablup/backend.ai-monitor-sentry) - Sentry exception collector


## Legacy Components

**[Media Library](https://github.com/lablup/backend.ai-media)** - Multi-media output support (no longer maintained)

**IDE Extensions** - (Deprecated: use in-kernel JupyterLab, VSCode Server or SSH instead)
- [VSCode Live Code Runner](https://github.com/lablup/vscode-live-code-runner)
- [Atom Live Code Runner](https://github.com/lablup/atom-live-code-runner)

## Development

### Building Packages

Build Python wheels or SCIE (Self-Contained Installable Executables):

```bash
./scripts/build-wheels.sh  # Build .whl packages
./scripts/build-scies.sh   # Build SCIE packages
```

Packages are placed in the `dist/` directory.

### Code Quality Hooks

Backend.AI uses Git pre-commit hooks to maintain code quality:

```bash
# Automatically runs on every commit:
# - Auto-formatting (pants fmt)
# - Linting (pants lint)

# Bypass hooks if needed (use sparingly)
git commit --no-verify
```

The pre-commit hook validates:
- Code style and formatting

Type checking and tests run in CI for comprehensive coverage.

See [AGENTS.md](AGENTS.md#hooks-and-code-quality) for the hook system documentation.

### Development Guide

For development setup, build system usage and contribution guidelines:
- [Development Setup](src/ai/backend/README.md#development-setup) - Python versions, Pants, dependency management
- [CONTRIBUTING.md](.github/CONTRIBUTING.md) - Contribution guidelines and development workflow
- [MIGRATION.md](MIGRATION.md) - Migration guide for major version updates

#### CLI Tab Completion for Development

To enable shell tab completion for the Backend.AI CLI during development:

```bash
# For bash/zsh (from repository root) - MUST use 'source', not execute directly
source scripts/setup-dev-completion.sh

# For fish shell
source scripts/setup-dev-completion.fish

# Or create a permanent alias
# bash/zsh:
echo 'alias bai-dev="cd /path/to/backend.ai && source scripts/setup-dev-completion.sh"' >> ~/.zshrc
# fish:
echo 'alias bai-dev="cd /path/to/backend.ai; and source scripts/setup-dev-completion.fish"' >> ~/.config/fish/config.fish
```

This enables tab completion for:
- `backend.ai <tab>` - Show all commands
- `backend.ai session <tab>` - Session management
- `backend.ai admin <tab>` - Admin operations
- `backend.ai --<tab>` - Global options

Supports the **bash**, **zsh** and **fish** shells.

## License

See the [LICENSE file](https://github.com/lablup/backend.ai/blob/main/LICENSE).
