# Backend.AI Agent with K8s 

The Backend.AI Agent is a small daemon that does:

* Reports the status and available resource slots of a worker to the manager
* Routes code execution requests to the designated kernel container
* Manages the lifecycle of kernel containers (create/monitor/destroy them)

## Package Structure

* `ai.backend`
  - `agent`: The agent package
    - `server`: The agent daemon which communicates with the manager and the Docker daemon


## Installation

First, you need **a working manager installation**.
For the detailed instructions on installing the manager, please refer
[the manager's README](https://github.com/lablup/backend.ai-manager/blob/master/README.md)
and come back here again.

### For development

#### Prequisites

* `libsnappy-dev` or `snappy-devel` system package depending on your distro
* Python 3.6 or higher with [pyenv](https://github.com/pyenv/pyenv)
and [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv) (optional but recommneded)
* Docker 18.03 or later with docker-compose (18.09 or later is recommended)
* Properly configured Kubeconfig file - should be located at `$HOME/.kube/config` or `$KUBECONFIG` path
* [Git LFS](https://git-lfs.github.com/) installed and configured
* [Backend.AI K8s controller](https://github.com/lablup/backend.ai-k8s-controller) installed and running without any error

#### One-shot installation

```sh
curl https://raw.githubusercontent.com/lablup/backend.ai-agent/feature/kube-integration/install-halfstack.sh | sudo bash -
```
This script automatically installs required components to run halfstack on a single-node cluster. This script is only for debian based distributions.

#### Common steps

Next, prepare the source clone of the agent and install from it as follows.

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

From now on, let's assume all shell commands are executed inside the virtualenv.

### Halfstack (single-node development & testing)

With the halfstack, you can run the agent simply.
Note that you need a working manager running with the halfstack already!

#### Recommended directory structure

* `backend.ai-dev`
  - `manager` (git clone from [the manager repo](https://github.com/lablup/backend.ai-manager))
  - `agent` (git clone from here, with branch `feature/kube-integration`)
  - `common` (git clone from [the common repo](https://github.com/lablup/backend.ai-common))

Install `backend.ai-common` as an editable package in the agent (and the manager) virtualenvs
to keep the codebase up-to-date.

```console
$ cd agent
$ pip install -U -e ../common
```

#### Steps

```console
$ mkdir -p "./scratches"
$ cp config/halfstack.toml ./agent.toml
```

Then, run it (for debugging, append a `--debug` flag):

```console
$ python -m ai.backen`d.agent.server
```

To run the agent-watcher:

```console
$ python -m ai.backend.agent.watcher
```

The watcher shares the same configuration TOML file with the agent.
Note that the watcher is only meaningful if the agent is installed as a systemd service
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

Only the first found one is used by the daemon.

The agent reads most other configurations from the etcd v3 server where the cluster
administrator or the Backend.AI manager stores all the necessary settings.

The etcd address and namespace must match with the manager to make the agent
paired and activated.
By specifying distinguished namespaces, you may share a single etcd cluster with multiple
separate Backend.AI clusters.

By default the agent uses `/var/cache/scratches` directory for making temporary
home directories used by kernel containers (the `/home/work` volume mounted in
containers).  Note that the directory must exist in prior and the agent-running
user must have ownership of it.  You can change the location by
`scratch-root` option in `agent.toml`.

### Setting up NFS-based vFolder for Backend.AI 

When you are trying to deploy Backend.AI Agent to K8s cluster from Cloud Provider(EKS, GKE, AKS, ...), you can provide NFS connection info directly to Backend.AI agent. All vFolder mounts will be set up and managed by K8s' PersistentVolume and PersistentVolumeClaim. To set up:

1. Add NFS connection information to `agent.toml`. Check `config/sample.toml` for details.
2. Mount NFS volume to Backend.AI manager's mount target provided when setting up Backend.AI manager (if you have deployed halfstack with one-shot installation script, just mount to `$HOME/vfroot`).

### Setting up CUDA support (experimental)
If [nVIDIA Device Plugin for K8s](https://github.com/NVIDIA/k8s-device-plugin) has been installed and running without any error, Backend.AI Agent automatically inspects available GPU and report it to manager.

### Running from a command line

The minimal command to execute:

```sh
python -m ai.backend.agent.server
```

For more arguments and options, run the command with `--help` option.

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

The manager and agent should run in the same local network or different
networks reachable via VPNs, whereas the manager's API service must be exposed to
the public network or another private network that users have access to.

The manager must be able to access TCP ports 6001, 6009, and 30000 to 31000 of the agents in default
configurations.  You can of course change those port numbers and ranges in the configuration.

| Manager-to-Agent TCP Ports | Usage |
|:--------------------------:|-------|
| 6001                       | ZeroMQ-based RPC calls from managers to agents |
| 6009                       | HTTP watcher API |
| 30000-31000                | Port pool for in-container services |

The operation of agent itself does not require both incoming/outgoing access to
the public Internet, but if the user's computation programs need the Internet, the docker containers
should be able to access the public Internet (maybe via some corporate firewalls).

| Agent-to-X TCP Ports     | Usage |
|:------------------------:|-------|
| manager:5002             | ZeroMQ-based event push from agents to the manager |
| etcd:2379                | etcd API access |
| redis:6379               | Redis API access |
| docker-registry:{80,443} | HTTP watcher API |
| (Other hosts)            | Depending on user program requirements |

The agent and K8s cluster should run in the same local network or VPC, and should be 
reachable to each other with appropriate Security Group if cluster is provisioned within Cloud Provicers. 
Agent uses NodePort service to communicate between agent and pod, so nodeport should be configured properly at K8s.
