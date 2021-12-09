Backend.AI
==========

[![PyPI release version](https://badge.fury.io/py/backend.ai.svg)](https://pypi.org/project/backend.ai/)
![Supported Python versions](https://img.shields.io/pypi/pyversions/backend.ai.svg)
[![Gitter](https://badges.gitter.im/lablup/backend.ai.svg)](https://gitter.im/lablup/backend.ai)

Backend.AI is a streamlined, container-based computing cluster orchestrator
that hosts diverse programming languages and popular computing/ML frameworks,
with pluggable heterogeneous accelerator support including CUDA and ROCM.
It allocates and isolates the underlying computing resources for multi-tenant
computation sessions on-demand or in batches with customizable job schedulers.
All its functions are exposed as REST/GraphQL/WebSocket APIs.


Server-side Components
----------------------

If you want to run a Backend.AI cluster on your own, you need to install and
configure the following server-side components.
All server-side components are licensed under LGPLv3 to promote non-proprietary open
innovation in the open-source community.

There is no obligation to open your service/system codes if you just run the
server-side components as-is (e.g., just run as daemons or import the components
without modification in your codes).
Please contact us (contact-at-lablup-com) for commercial consulting and more
licensing details/options about individual use-cases.

For details about server installation and configuration, please visit [our
documentation](http://docs.backend.ai).

### Manager with API Gateway

It routes external API requests from front-end services to individual agents.
It also monitors and scales the cluster of multiple agents (a few tens to hundreds).

* https://github.com/lablup/backend.ai-manager
  * Package namespace: `ai.backend.gateway` and `ai.backend.manager`
  * Plugin interfaces
    - `backendai_scheduler_v10`
    - `backendai_hook_v10`
    - `backendai_webapp_v10`
    - `backendai_monitor_stats_v10`
    - `backendai_monitor_error_v10`

### Agent

It manages individual server instances and launches/destroys Docker containers where
REPL daemons (kernels) run.
Each agent on a new EC2 instance self-registers itself to the instance registry via
heartbeats.

* https://github.com/lablup/backend.ai-agent
  * Package namespace: `ai.backend.agent`
  * Plugin interfaces
    - `backendai_accelerator_v12`
    - `backendai_monitor_stats_v10`
    - `backendai_monitor_error_v10`
    - `backendai_krunner_v10`
* https://github.com/lablup/backend.ai-accelerator-cuda (CUDA accelerator plugin)
  * Package namespace: `ai.backend.acceelrator.cuda`
* https://github.com/lablup/backend.ai-accelerator-cuda-mock (CUDA mockup plugin)
  * Package namespace: `ai.backend.acceelrator.cuda`
  * This emulates the presence of CUDA devices without actual CUDA devices,
    so that developers can work on CUDA integration without real GPUs.
* https://github.com/lablup/backend.ai-accelerator-rocm (ROCM accelerator plugin)
  * Package namespace: `ai.backend.acceelrator.rocm`

### Server-side common plugins (for both manager and agents)

* https://github.com/lablup/backend.ai-stats-monitor
  - Statistics collector based on the Datadog API
  - Package namespace: `ai.backend.monitor.stats`
* https://github.com/lablup/backend.ai-error-monitor
  - Exception collector based on the Sentry API
  - Package namespace: `ai.backend.monitor.error`

### Kernels

A set of small ZeroMQ-based REPL daemons in various programming languages and
configurations.

* https://github.com/lablup/backend.ai-kernel-runner
   * Package namespace: `ai.backend.kernel`
   * A common interface for the agent to deal with various language runtimes
* https://github.com/lablup/backend.ai-kernels
   * Runtime-specific recipes to build the Docker images (Dockerfile)

### Jail

A programmable sandbox implemented using ptrace-based sytem call filtering written in
Go.

* https://github.com/lablup/backend.ai-jail

### Hook

A set of libc overrides for resource control and web-based interactive stdin (paired
with agents).

* https://github.com/lablup/backend.ai-hook

### Commons

A collection of utility modules commonly shared throughout Backend.AI projects.

* Package namespaces: `ai.backend.common`
* https://github.com/lablup/backend.ai-common


Client-side Components
----------------------

### Client SDK Libraries

We offer client SDKs in popular programming languages.
These SDKs are freely available with MIT License to ease integration with both
commercial and non-commercial software products and services.

* Python (provides the command-line interface)
   * `pip install backend.ai-client`
   * https://github.com/lablup/backend.ai-client-py
* Java
   * Currently only available via GitHub releases
   * https://github.com/lablup/backend.ai-client-java
* Javascript
   * `npm install backend.ai-client`
   * https://github.com/lablup/backend.ai-client-js
* PHP (under preparation)
   * `composer require lablup/backend.ai-client`
   * https://github.com/lablup/backend.ai-client-php

### Media

The front-end support libraries to handle multi-media outputs (e.g., SVG plots,
animated vector graphics)

* The Python package (`lablup`) is installed *inside* kernel containers.
* To interpret and display media generated by the Python package, you need to load
  the Javascript part in the front-end.
* https://github.com/lablup/backend.ai-media

Interacting with computation sessions
-------------------------------------

Backend.AI provides websocket tunneling into individual computation sessions (containers),
so that users can use their browsers and client CLI to access in-container applications directly
in a secure way.

* Jupyter Kernel: data scientists' favorite tool
   * Most container sessions have intrinsic Jupyter and JupyterLab support.
* Web-based terminal
   * All container sessions have intrinsic ttyd support.
* SSH
   * All container sessions have intrinsic SSH/SFTP/SCP support with auto-generated per-user SSH keypair.
     PyCharm and other IDEs can use on-demand sessions using SSH remote interpreters.
* VSCode (coming soon)
   * Most container sessions have intrinsic web-based VSCode support.

Integrations with IDEs and Editors
----------------------------------

* Visual Studio Code Extension
   * Search “Live Code Runner” among VSCode extensions.
   * https://github.com/lablup/vscode-live-code-runner
* Atom Editor plugin
   * Search “Live Code Runner” among Atom plugins.
   * https://github.com/lablup/atom-live-code-runner

Storage management
------------------

Backend.AI provides an abstraction layer on top of existing network-based storages
(e.g., NFS/SMB), called vfolders (virtual folders).
Each vfolder works like a cloud storage that can be mounted into any computation
sessions and shared between users and user groups with differentiated privileges.

License
-------

Refer to [LICENSE file](https://github.com/lablup/backend.ai/blob/main/LICENSE).
