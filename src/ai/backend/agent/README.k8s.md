# Backend.AI Agent with Kubernetes

The Backend.AI Agent is a small daemon that does the following:

* Reports the status and available resource slots of a worker to the manager
* Routes code execution requests to the designated kernel container
* Manages the lifecycle of kernel containers (creates, monitors, and destroys them)

## Package Structure

* `ai.backend`
  - `agent`: The agent package
    - `server`: The agent daemon which communicates with the manager and the Docker daemon


## Installation

First, you need **a working manager installation**.
For detailed instructions on installing the manager, see
[the manager's README](https://github.com/lablup/backend.ai-manager/blob/master/README.md)
and return here.

### For development

#### Prerequisites

* Python 3.6 or higher with [pyenv](https://github.com/pyenv/pyenv)
and [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv) (optional but recommended)
* Docker 18.03 or later with docker-compose (18.09 or later is recommended)
* A properly configured kubeconfig file that should be located at `$HOME/.kube/config` or the `$KUBECONFIG` path
* [Git LFS](https://git-lfs.github.com/) installed and configured
* [Backend.AI K8s controller](https://github.com/lablup/backend.ai-k8s-controller) installed and running without errors

#### One-shot installation

```sh
curl https://raw.githubusercontent.com/lablup/backend.ai-agent/feature/kube-integration/install-halfstack.sh | sudo bash -
```
This script automatically installs the components required to run halfstack on a single-node cluster. It supports Debian-based distributions only.

#### Common steps

Prepare a source clone of the agent and install from it:

```console
$ git clone https://github.com/lablup/backend.ai-agent agent
$ cd agent
$ git checkout feature/kube-integration
$ git lfs pull
$ pyenv virtualenv venv-agent
$ pyenv local venv-agent
$ pip install -U pip setuptools
$ pip install -U -r requirements-dev.txt
```

All shell commands below run inside the virtualenv.

### Halfstack (single-node development and testing)

With halfstack, you can run the agent directly.
A working manager must already run on the halfstack.

#### Recommended directory structure

* `backend.ai-dev`
  - `manager` (git clone from [the manager repo](https://github.com/lablup/backend.ai-manager))
  - `agent` (git clone from here, with branch `feature/kube-integration`)
  - `common` (git clone from [the common repo](https://github.com/lablup/backend.ai-common))

Install `backend.ai-common` as an editable package in the agent and manager virtualenvs
to keep the codebase current.

```console
$ cd agent
$ pip install -U -e ../common
```

#### Steps

```console
$ mkdir -p "./scratches"
$ cp config/halfstack.toml ./agent.toml
```

Then run the agent. Append `--debug` for debugging:

```console
$ python -m ai.backen`d.agent.server
```

To run the agent watcher:

```console
$ python -m ai.backend.agent.watcher
```

The watcher reads the same TOML configuration file as the agent.
The watcher is meaningful only when the agent is installed as a systemd service
named `backendai-agent.service`.

To run tests:

```console
$ python -m flake8 src tests
$ python -m pytest -m 'not integration' tests
```




## Deployment

### Configuration

Put a TOML-formatted agent configuration (see the sample in `config/sample.toml`)
in one of the following locations:

 * `agent.toml` (current working directory)
 * `~/.config/backend.ai/agent.toml` (user-config directory)
 * `/etc/backend.ai/agent.toml` (system-config directory)

Only the first file found is used by the daemon.

The agent reads most other configurations from the etcd v3 server where the cluster
administrator or the Backend.AI manager stores all the necessary settings.

The etcd address and namespace must match the manager for the agent to be
paired and activated.
By specifying distinct namespaces, you may share a single etcd cluster with multiple
separate Backend.AI clusters.

By default the agent uses the `/var/cache/scratches` directory for the temporary
home directories of kernel containers (the `/home/work` volume mounted in
containers).  The directory must exist beforehand and the user that runs the agent must own it.  You can change the location with the
`scratch-root` option in `agent.toml`.

### Setting up an NFS-based vfolder for Backend.AI

When you deploy the Backend.AI Agent to a Kubernetes cluster on a cloud provider (EKS, GKE, AKS, and others), you can pass NFS connection information directly to the agent. Kubernetes and its PersistentVolume and PersistentVolumeClaim set up and manage all vfolder mounts. To set up:

1. Add NFS connection information to `agent.toml`. See `config/sample.toml` for details.
2. Mount the NFS volume at the manager's mount target, which is provided when you set up the Backend.AI manager. If you deployed halfstack with the one-shot installation script, mount at `$HOME/vfroot`.

### Setting up CUDA support (experimental)
If the [NVIDIA Device Plugin for K8s](https://github.com/NVIDIA/k8s-device-plugin) is installed and running without errors, the Backend.AI Agent detects the available GPUs automatically and reports them to the manager.

### Running from a command line

The minimal command is:

```sh
python -m ai.backend.agent.server
```

For more arguments and options, run the command with the `--help` option.

### Example config for agent server/instances

`/etc/supervisor/conf.d/agent.conf`:

```dosini
[program:backend.ai-agent]
user = user
stopsignal = TERM
stopasgroup = true
command = /home/user/run-agent.sh
```

`/home/user/run-agent.sh`:

```sh
#!/bin/sh
source /home/user/venv-agent/bin/activate
exec python -m ai.backend.agent.server
```

### Networking

The manager and the agent should run in the same local network, or in different
networks reachable through VPNs. The manager's API service must be exposed to
the public network or to another private network that users can access.

The manager must be able to reach TCP ports 6001, 6009, and 30000 to 31000 of the agents in the default
configuration.  You can of course change these port numbers and ranges in the configuration.

| Manager-to-Agent TCP Ports | Usage |
|:--------------------------:|-------|
| 6001                       | ZeroMQ-based RPC calls from managers to agents |
| 6009                       | HTTP watcher API |
| 30000-31000                | Port pool for in-container services |

The agent itself needs no incoming or outgoing access to the public Internet. If the user's programs
need the Internet, the Docker containers should be able to reach the public Internet, possibly through
corporate firewalls.

| Agent-to-X TCP Ports     | Usage |
|:------------------------:|-------|
| manager:5002             | ZeroMQ-based event push from agents to the manager |
| etcd:2379                | etcd API access |
| redis:6379               | Valkey/Redis API access |
| docker-registry:{80,443} | HTTP watcher API |
| (Other hosts)            | Depending on user program requirements |

The agent and the Kubernetes cluster should run in the same local network or VPC and should be
reachable from each other with an appropriate Security Group when the cluster is provisioned on a cloud provider.
The agent communicates with pods through a NodePort service, so NodePort should be configured correctly in Kubernetes.
