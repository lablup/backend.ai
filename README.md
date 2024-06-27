Backend.AI
==========

[![PyPI release version](https://badge.fury.io/py/backend.ai-manager.svg)](https://pypi.org/project/backend.ai-manager/)
![Supported Python versions](https://img.shields.io/pypi/pyversions/backend.ai-manager.svg)
![Wheels](https://img.shields.io/pypi/wheel/backend.ai-manager.svg)
[![Gitter](https://badges.gitter.im/lablup/backend.ai.svg)](https://gitter.im/lablup/backend.ai)

Backend.AI is a streamlined, container-based computing cluster platform
that hosts popular computing/ML frameworks and diverse programming languages,
with pluggable heterogeneous accelerator support including CUDA GPU, ROCm GPU, TPU, IPU and other NPUs.

It allocates and isolates the underlying computing resources for multi-tenant
computation sessions on-demand or in batches with customizable job schedulers with its own orchestrator.
All its functions are exposed as REST/GraphQL/WebSocket APIs.


Contents in This Repository
---------------------------

This repository contains all open-source server-side components and the client SDK for Python
as a reference implementation of API clients.

### Directory Structure

* `src/ai/backend/`: Source codes
  - `manager/`: Manager
  - `manager/api`: Manager API handlers
  - `agent/`: Agent
  - `agent/docker/`: Agent's Docker backend
  - `agent/k8s/`: Agent's Kubernetes backend
  - `kernel/`: Agent's kernel runner counterpart
  - `runner/`: Agent's in-kernel prebuilt binaries
  - `helpers/`: Agent's in-kernel helper package
  - `common/`: Shared utilities
  - `client/`: Client SDK
  - `cli/`: Unified CLI for all components
  - `storage/`: Storage proxy
  - `storage/api`: Storage proxy's manager-facing and client-facing APIs
  - `web/`: Web UI server
    - `static/`: Backend.AI WebUI release artifacts
  - `plugin/`: Plugin subsystem
  - `test/`: Integration test suite
  - `testutils/`: Shared utilities used by unit tests
  - `meta/`: Legacy meta package
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


Getting Started
---------------

### Installation for Single-node Development

Run `scripts/install-dev.sh` after cloning this repository.

This script checks availability of all required dependencies such as Docker and bootstrap a development
setup.  Note that it requires `sudo` and a modern Python installed in the host system based on Linux
(Debian/RHEL-likes) or macOS.

### Installation for Multi-node Tests &amp; Production

Please consult [our documentation](http://docs.backend.ai) for community-supported materials.
Contact the sales team (contact@lablup.com) for professional paid support and deployment options.

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


Major Components
----------------

### Manager

It routes external API requests from front-end services to individual agents.
It also monitors and scales the cluster of multiple agents (a few tens to hundreds).

* `src/ai/backend/manager`
  * [README](https://github.com/lablup/backend.ai/blob/main/src/ai/backend/manager/README.md)
  * Legacy per-pkg repo: https://github.com/lablup/backend.ai-manager
  * Available plugin interfaces
    - `backendai_scheduler_v10`
    - `backendai_hook_v20`
    - `backendai_webapp_v20`
    - `backendai_monitor_stats_v10`
    - `backendai_monitor_error_v10`

### Agent

It manages individual server instances and launches/destroys Docker containers where
REPL daemons (kernels) run.
Each agent on a new EC2 instance self-registers itself to the instance registry via
heartbeats.

* `src/ai/backend/agent`
  * [README](https://github.com/lablup/backend.ai/blob/main/src/ai/backend/agent/README.md)
  * Legacy per-pkg repo: https://github.com/lablup/backend.ai-agent
  * Available plugin interfaces
    - `backendai_accelerator_v21`
    - `backendai_monitor_stats_v10`
    - `backendai_monitor_error_v10`

### Storage Proxy

It provides a unified abstraction over multiple different network storage devices with
vendor-specific enhancements such as real-time performance metrics and filesystem operation
acceleration APIs.

* `src/ai/backend/storage`
  * [README](https://github.com/lablup/backend.ai/blob/main/src/ai/backend/storage/README.md)
  * Legacy per-pkg repo: https://github.com/lablup/backend.ai-storage-proxy

### Webserver

It hosts the SPA (single-page application) packaged from our web UI codebase for end-users
and basic administration tasks.

* `src/ai/backend/web`
  * [README](https://github.com/lablup/backend.ai/blob/main/src/ai/backend/web/README.md)
  * Legacy per-pkg repo: https://github.com/lablup/backend.ai-webserver

**Synchronizing the static Backend.AI WebUI version:**
```console
$ scripts/download-webui-release.sh <target version to download>
```

### Kernels

Computing environment recipes (Dockerfile) to build the container images to execute
on top of the Backend.AI platform.

* https://github.com/lablup/backend.ai-kernels

### Jail

A programmable sandbox implemented using ptrace-based system call filtering written in Rust.

* https://github.com/lablup/backend.ai-jail

### Hook

A set of libc overrides for resource control and web-based interactive stdin (paired
with agents).

* https://github.com/lablup/backend.ai-hook

### Client SDK Libraries

We offer client SDKs in popular programming languages.
These SDKs are freely available with MIT License to ease integration with both
commercial and non-commercial software products and services.

* Python (provides the command-line interface)
   * `pip install backend.ai-client`
   * https://github.com/lablup/backend.ai/tree/main/src/ai/backend/client
* Java
   * Currently only available via GitHub releases
   * https://github.com/lablup/backend.ai-client-java
* Javascript
   * `npm install backend.ai-client`
   * https://github.com/lablup/backend.ai-client-js
* PHP (under preparation)
   * `composer require lablup/backend.ai-client`
   * https://github.com/lablup/backend.ai-client-php


Plugins
-------

* `backendai_accelerator_v21`
  - [`ai.backend.accelerator.cuda`](https://github.com/lablup/backend.ai/tree/main/src/ai/backend/accelerator/cuda_open): CUDA accelerator plugin
  - [`ai.backend.accelerator.cuda` (mock)](https://github.com/lablup/backend.ai/tree/main/src/ai/backend/accelerator/cuda_mock): CUDA mockup plugin
    - This emulates the presence of CUDA devices without actual CUDA devices,
      so that developers can work on CUDA integration without real GPUs.
  - [`ai.backend.accelerator.rocm`](): ROCm accelerator plugin
  - More available in the enterprise edition!
* `backendai_monitor_stats_v10`
  - [`ai.backend.monitor.stats`](https://github.com/lablup/backend.ai-monitor-datadog)
    - Statistics collector based on the Datadog API
* `backendai_monitor_error_v10`
  - [`ai.backend.monitor.error`](https://github.com/lablup/backend.ai-monitor-sentry)
    - Exception collector based on the Sentry API


Legacy Components
-----------------

These components still exist but are no longer actively maintained.

### Media

The front-end support libraries to handle multi-media outputs (e.g., SVG plots,
animated vector graphics)

* The Python package (`lablup`) is installed *inside* kernel containers.
* To interpret and display media generated by the Python package, you need to load
  the Javascript part in the front-end.
* https://github.com/lablup/backend.ai-media


### IDE and Editor Extensions

* Visual Studio Code Extension
   * Search “Live Code Runner” among VSCode extensions.
   * https://github.com/lablup/vscode-live-code-runner
* Atom Editor plugin
   * Search “Live Code Runner” among Atom plugins.
   * https://github.com/lablup/atom-live-code-runner

We now recommend using in-kernel applications such as Jupyter Lab, Visual Studio Code Server,
or native SSH connection to kernels via our client SDK or desktop apps.

Python Version Compatibility
----------------------------

| Backend.AI Core Version | Python Version | Pantsbuild version |
|:-----------------------:|:--------------:|:------------------:|
| 24.03.x / 24.09.x       | 3.12.x         | 2.21.x             |
| 23.03.x / 23.09.x       | 3.11.x         | 2.19.x             |
| 22.03.x / 22.09.x       | 3.10.x         |                    |
| 21.03.x / 21.09.x       | 3.8.x          |                    |


License
-------

Refer to [LICENSE file](https://github.com/lablup/backend.ai/blob/main/LICENSE).
