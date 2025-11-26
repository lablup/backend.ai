Backend.AI
==========

[![PyPI release version](https://badge.fury.io/py/backend.ai-manager.svg)](https://pypi.org/project/backend.ai-manager/)
![Supported Python versions](https://img.shields.io/pypi/pyversions/backend.ai-manager.svg)
![Wheels](https://img.shields.io/pypi/wheel/backend.ai-manager.svg)
[![Gitter](https://badges.gitter.im/lablup/backend.ai.svg)](https://gitter.im/lablup/backend.ai)

Backend.AI is a streamlined, container-based computing cluster platform
that hosts popular computing/ML frameworks and diverse programming languages,
with pluggable heterogeneous accelerator support including CUDA GPU, ROCm GPU,
Rebellions, FuriosaAI, HyperAccel, Google TPU, Graphcore IPU and other NPUs.

It allocates and isolates the underlying computing resources for multi-tenant
computation sessions on-demand or in batches with customizable job schedulers with its own orchestrator named "Sokovan".

All its functions are exposed as REST and GraphQL APIs.


Requirements
------------

### Python & Build Tools

- **Python**: 3.13.x (main branch requires CPython 3.13.7)
- **Pantsbuild**: 2.27.x
- See [full version compatibility table](src/ai/backend/README.md#development-setup)

### Infrastructure

**Required**:
- Docker 20.10+ (with Compose v2)
- PostgreSQL 16+ (tested with 16.3)
- Redis 7.2+ (tested with 7.2.11)
- etcd 3.5+ (tested with 3.5.14)
- Prometheus 3.x (tested with 3.1.0)

**Recommended** (for observability):
- Grafana 11.x (tested with 11.4.0)
- Loki 3.x (tested with 3.5.0)
- Tempo 2.x (tested with 2.7.2)
- OpenTelemetry Collector

→ Detailed infrastructure setup: [Infrastructure Documentation](src/ai/backend/README.md#infrastructure-layer)

### System

- **OS**: Linux (Debian/RHEL-based) or macOS
- **Permissions**: sudo access for installation
- **Resources**: 4+ CPU cores, 8GB+ RAM recommended for development


Getting Started
---------------

### Quick Start (Development)

#### 1. Clone and Install

```bash
git clone https://github.com/lablup/backend.ai.git
cd backend.ai
./scripts/install-dev.sh
```

This script will:
- Check required dependencies (Docker, Python, etc.)
- Set up Python virtual environment with Pantsbuild
- Start halfstack infrastructure (PostgreSQL, Redis, etcd, Grafana, etc.)
- Initialize database schemas
- Create default API keypairs and user accounts

#### 2. Start Backend.AI Services

Start each component in separate terminals:

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
./py -m ai.backend.storage.server
```

**Web Server** (Terminal 4):
```bash
./py -m ai.backend.web.server
```

**App Proxy** (Terminal 5-6, optional for in-container service access):
```bash
./backend.ai app-proxy-coordinator start-server --debug
./backend.ai app-proxy-worker start-server --debug
```

#### 3. Run Your First Session

Set up client environment:
```bash
source env-local-user-session.sh
```

Run a simple Python session:
```bash
./backend.ai run python -c "print('Hello Backend.AI!')"
```

Or access Web UI at **http://localhost:8090** with credentials from `env-local-*.sh` files.

### Accessing Compute Sessions (aka Kernels)

Backend.AI provides websocket tunneling into individual computation sessions (containers),
so that users can use their browsers and client CLI to access in-container applications directly
in a secure way.

* Jupyter: data scientists' favorite tool
   * Most container images have intrinsic Jupyter and JupyterLab support.
* Web-based terminal
   * All container sessions have intrinsic ttyd support.
* SSH
   * All container sessions have intrinsic SSH/SFTP/SCP support with auto-generated per-user SSH keypair.
     PyCharm and other IDEs can use on-demand sessions using SSH remote interpreters.
* VSCode
   * Most container sessions have intrinsic web-based VSCode support.

### Working with Storage

Backend.AI provides an abstraction layer on top of existing network-based storages
(e.g., NFS/SMB), called vfolders (virtual folders).
Each vfolder works like a cloud storage that can be mounted into any computation
sessions and shared between users and user groups with differentiated privileges.

### Installation for Multi-node Tests & Production

Please consult [our documentation](http://docs.backend.ai) for community-supported materials.
Contact the sales team (contact@lablup.com) for professional paid support and deployment options.


Architecture
------------

For comprehensive system architecture, component interactions, and infrastructure details, see:

**[Component Architecture Documentation](src/ai/backend/README.md)**

This document covers:
- System architecture diagrams and component flow
- Port numbers and infrastructure setup
- Component dependencies and communication protocols
- Development and production environment configuration


Contents in This Repository
---------------------------

This repository contains all open-source server-side components and the client SDK for Python
as a reference implementation of API clients.

### Directory Structure

* `src/ai/backend/`: Source codes
  - `manager/`: Manager as the cluster control-plane
  - `manager/api`: Manager API handlers
  - `account_manager/`: Unified user profile and SSO management
  - `agent/`: Agent as per-node controller
  - `agent/docker/`: Agent's Docker backend
  - `agent/k8s/`: Agent's Kubernetes backend
  - `agent/dummy/`: Agent's dummy backend
  - `kernel/`: Agent's kernel runner counterpart
  - `runner/`: Agent's in-kernel prebuilt binaries
  - `helpers/`: Agent's in-kernel helper package
  - `common/`: Shared utilities
  - `client/`: Client SDK
  - `cli/`: Unified CLI for all components
  - `install/`: SCIE-based TUI installer
  - `storage/`: Storage proxy for offloading storage operations
  - `storage/api`: Storage proxy's manager-facing and client-facing APIs
  - `appproxy/`: App proxy for accessing container apps from outside
  - `appproxy/coordinator`: App proxy coordinator who provisions routing circuits
  - `appproxy/worker`: App proxy worker who forwards the traffic
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
* `plugins/`: A directory to place plugins such as accelerators, monitors, etc.
* `scripts/`: Scripts to assist development workflows
  - `install-dev.sh`: The single-node development setup script from the working copy
* `stubs/`: Type annotation stub packages written by us
* `tools/`: A directory to host Pants-related tooling
* `dist/`: A directory to put build artifacts (.whl files) and Pants-exported virtualenvs
* `changes/`: News fragments for towncrier
* `pants.toml`: The Pants configuration
* `pyproject.toml`: Tooling configuration (towncrier, pytest, mypy)
* `BUILD`: The root build config file
* `**/BUILD`: Per-directory build config files
* `BUILD_ROOT`: An indicator to mark the build root directory for Pants
* `CLAUDE.md`: The steering guide for agent-assisted development
* `requirements.txt`: The unified requirements file
* `*.lock`, `tools/*.lock`: The dependency lock files
* `docker-compose.*.yml`: Per-version recommended halfstack container configs
* `README.md`: This file
* `MIGRATION.md`: The migration guide for updating between major releases
* `VERSION`: The unified version declaration

Server-side components are licensed under LGPLv3 to promote non-proprietary open
innovation in the open-source community while other shared libraries and client SDKs
are distributed under the MIT license.

There is no obligation to open your service/system codes if you just run the
server-side components as-is (e.g., just run as daemons or import the components
without modification in your codes).
Please contact us (contact-at-lablup-com) for commercial consulting and more
licensing details/options about individual use-cases.


Major Components
----------------

Backend.AI consists of the following core components:

### Server-Side Components

**[Manager](src/ai/backend/manager/README.md)** - Central API gateway and orchestrator
- Routes REST/GraphQL requests and orchestrates cluster operations
- Session scheduling via Sokovan orchestrator
- User authentication and RBAC authorization
- Plugin interfaces: `backendai_scheduler_v10`, `backendai_agentselector_v10`, `backendai_hook_v20`, `backendai_webapp_v20`, `backendai_monitor_stats_v10`, `backendai_monitor_error_v10`
- Legacy repo: https://github.com/lablup/backend.ai-manager

**[Agent](src/ai/backend/agent/README.md)** - Kernel lifecycle management on compute nodes
- Manages Docker containers (kernels) on individual nodes
- Self-registers to cluster via heartbeats
- Plugin interfaces: `backendai_accelerator_v21`, `backendai_monitor_stats_v10`, `backendai_monitor_error_v10`
- Legacy repo: https://github.com/lablup/backend.ai-agent

**[Storage Proxy](src/ai/backend/storage/README.md)** - Virtual folder and storage backend abstraction
- Unified interface for multiple storage backends
- Real-time performance metrics and acceleration APIs
- Legacy repo: https://github.com/lablup/backend.ai-storage-proxy

**[Webserver](src/ai/backend/web/README.md)** - Web UI hosting and session management
- Hosts Backend.AI WebUI (SPA)
- Session management and API request signing
- Legacy repo: https://github.com/lablup/backend.ai-webserver

**Synchronizing the static Backend.AI WebUI version:**
```console
$ scripts/download-webui-release.sh <target version to download>
```

**[App Proxy](src/ai/backend/appproxy/coordinator/README.md)** - Service routing and load balancing
- Routes traffic to in-container services (Jupyter, VSCode, etc.)
- Dynamic circuit provisioning and health monitoring

### Container Runtime Components

**[Kernels](https://github.com/lablup/backend.ai-kernels)** - Container image recipes
- Dockerfile-based computing environment recipes
- Support for popular ML frameworks and programming languages

**[Jail](https://github.com/lablup/backend.ai-jail)** - Programmable sandbox (Rust)
- ptrace-based system call filtering
- Resource control and security enforcement

**[Hook](https://github.com/lablup/backend.ai-hook)** - In-container runtime library
- libc overrides for resource control
- Web-based interactive stdin support

### Client SDK Libraries

We offer client SDKs in popular programming languages (MIT License):

- **Python** - `pip install backend.ai-client` | [GitHub](src/ai/backend/client) | Includes CLI
- **Java** - [Releases](https://github.com/lablup/backend.ai-client-java)
- **Javascript** - `npm install backend.ai-client` | [GitHub](https://github.com/lablup/backend.ai-client-js)
- **PHP** - (under preparation) `composer require lablup/backend.ai-client` | [GitHub](https://github.com/lablup/backend.ai-client-php)


Plugins
-------

Backend.AI supports plugin-based extensibility via Python package entrypoints:

**Accelerator Plugins** (`backendai_accelerator_v21`)
- [CUDA](src/ai/backend/accelerator/cuda_open) - NVIDIA GPU support
- [CUDA Mock](src/ai/backend/accelerator/cuda_mock) - Development without actual GPUs
- [ROCm](src/ai/backend/accelerator/rocm) - AMD GPU support
- [Furiosa](src/ai/backend/accelerator/furiosa) - Furiosa NPU (Warboy / RNGD) support
- [Hyperaccel](src/ai/backend/accelerator/hyperaccel) - Hyperaccel LPU support
- [IPU](src/ai/backend/accelerator/ipu) - Graphcore IPU support
- [Rebellions](src/ai/backend/accelerator/rebellions) - Rebellions NPU (ATOM, ATOM+, ATOM Max) support
- [Tenstorrent](src/ai/backend/accelerator/tenstorrent) - Tenstorrent NPU (Wormhole, Blackhole) support
- [TPU](src/ai/backend/accelerator/tpu) - Google TPU (v2, v3) support

**Monitoring Plugins**
- [`backendai_monitor_stats_v10`](https://github.com/lablup/backend.ai-monitor-datadog) - Datadog statistics collector
- [`backendai_monitor_error_v10`](https://github.com/lablup/backend.ai-monitor-sentry) - Sentry exception collector


Legacy Components
-----------------

**[Media Library](https://github.com/lablup/backend.ai-media)** - Multi-media output support (no longer maintained)

**IDE Extensions** - (Deprecated: Use in-kernel Jupyter Lab, VSCode Server, or SSH instead)
- [VSCode Live Code Runner](https://github.com/lablup/vscode-live-code-runner)
- [Atom Live Code Runner](https://github.com/lablup/atom-live-code-runner)

Development
-----------

### Building Packages

Build Python wheels or SCIE (Self-Contained Installable Executables):

```bash
./scripts/build-wheels.sh  # Build .whl packages
./scripts/build-scies.sh   # Build SCIE packages
```

Packages are placed in `dist/` directory.

### Code Quality Hooks

Backend.AI uses Git pre-commit hooks to maintain code quality:

```bash
# Automatically runs on every commit:
# - Linting (pants lint)
# - Type checking (pants check)

# Bypass hooks if needed (use sparingly)
git commit --no-verify
```

The pre-commit hook validates:
- Code style and formatting
- Type annotations

Tests run in CI for comprehensive coverage.

See [CLAUDE.md](CLAUDE.md#hooks-and-code-quality) for detailed hook system documentation.

### Development Guide

For detailed development setup, build system usage, and contribution guidelines:
- [Development Setup](src/ai/backend/README.md#development-setup) - Python versions, Pantsbuild, dependency management
- [CONTRIBUTING.md](.github/CONTRIBUTING.md) - Contribution guidelines and development workflow
- [MIGRATION.md](MIGRATION.md) - Migration guide for major version updates

License
-------

Refer to [LICENSE file](https://github.com/lablup/backend.ai/blob/main/LICENSE).
