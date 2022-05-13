# Backend.AI Agent

The Backend.AI Agent is a small daemon that does:

* Reports the status and available resource slots of a worker to the manager
* Routes code execution requests to the designated kernel container
* Manages the lifecycle of kernel containers (create/monitor/destroy them)

## Package Structure

* `ai.backend`
  - `agent`: The agent package
    - `docker`: A docker-based backend implementation for the kernel lifecycle interface.
    - `server`: The agent daemon which communicates with the manager and the Docker daemon
    - `watcher`: A side-by-side daemon which provides a separate HTTP endpoint for accessing the status
      information of the agent daemon and manipulation of the agent's systemd service
  - `helpers`: A utility package that is available as `ai.backend.helpers` *inside* Python-based containers
  - `kernel`: Language-specific runtimes (mostly ipykernel client adaptor) which run *inside* containers
  - `runner`: Auxiliary components (usually self-contained binaries) mounted *inside* contaienrs


## Installation

Please visit [the installation guides](https://github.com/lablup/backend.ai/wiki).


### Kernel/system configuration

#### Recommended kernel parameters in the bootloader (e.g., Grub):

```
cgroup_enable=memory swapaccount=1
```

#### Recommended resource limits:

**`/etc/security/limits.conf`**
```
root hard nofile 512000
root soft nofile 512000
root hard nproc 65536
root soft nproc 65536
user hard nofile 512000
user soft nofile 512000
user hard nproc 65536
user soft nproc 65536
```

**sysctl**
```
fs.file-max=2048000
fs.inotify.max_user_watches=524288
net.core.somaxconn=1024
net.ipv4.tcp_max_syn_backlog=1024
net.ipv4.tcp_slow_start_after_idle=0
net.ipv4.tcp_fin_timeout=10
net.ipv4.tcp_window_scaling=1
net.ipv4.tcp_tw_reuse=1
net.ipv4.tcp_early_retrans=1
net.ipv4.ip_local_port_range=40000 65000
net.core.rmem_max=16777216
net.core.wmem_max=16777216
net.ipv4.tcp_rmem=4096 12582912 16777216
net.ipv4.tcp_wmem=4096 12582912 16777216
net.netfilter.nf_conntrack_max=10485760
net.netfilter.nf_conntrack_tcp_timeout_established=432000
net.netfilter.nf_conntrack_tcp_timeout_close_wait=10
net.netfilter.nf_conntrack_tcp_timeout_fin_wait=10
net.netfilter.nf_conntrack_tcp_timeout_time_wait=10
```

The `ip_local_port_range` should not overlap with the container port range pool
(default: 30000 to 31000).

To apply netfilter settings during the boot time, you may need to add `nf_conntrack` to `/etc/modules`
so that `sysctl` could set the `net.netfilter.nf_conntrack_*` values.


### For development

#### Prerequisites

* `libsnappy-dev` or `snappy-devel` system package depending on your distro
* Python 3.6 or higher with [pyenv](https://github.com/pyenv/pyenv)
and [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv) (optional but recommneded)
* Docker 18.03 or later with docker-compose (18.09 or later is recommended)

First, you need **a working manager installation**.
For the detailed instructions on installing the manager, please refer
[the manager's README](https://github.com/lablup/backend.ai-manager/blob/master/README.md)
and come back here again.

#### Preparing working copy

Install and activate [`git-lfs`](https://git-lfs.github.com/) to work with pre-built binaries in
`src/ai/backend/runner`.

```console
$ git lfs install
```

Next, prepare the source clone of the agent and install from it as follows.
`pyenv` is just a recommendation; you may use other virtualenv management tools.

```console
$ git clone https://github.com/lablup/backend.ai-agent agent
$ cd agent
$ pyenv virtualenv venv-agent
$ pyenv local venv-agent
$ pip install -U pip setuptools
$ pip install -U -r requirements/dev.txt
```

### Linting

We use `flake8` and `mypy` to statically check our code styles and type consistency.
Enable those linters in your favorite IDE or editor.

### Halfstack (single-node development & testing)

With the halfstack, you can run the agent simply.
Note that you need a working manager running with the halfstack already!

#### Recommended directory structure

* `backend.ai-dev`
  - `manager` (git clone from [the manager repo](https://github.com/lablup/backend.ai-manager))
  - `agent` (git clone from here)
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

If you're running agent under linux, make sure you've set appropriate iptables rule 
before starting agent. This can be done by executing script `scripts/update-metadata-iptables.sh` 
before each agent start.

Then, run it (for debugging, append a `--debug` flag):

```console
$ python -m ai.backend.agent.server
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

### Running from a command line

The minimal command to execute:

```sh
python -m ai.backend.agent.server
python -m ai.backend.agent.watcher
```

For more arguments and options, run the command with `--help` option.

### Example config for systemd

`/etc/systemd/system/backendai-agent.service`:

```dosini
[Unit]
Description=Backend.AI Agent
Requires=docker.service
After=network.target remote-fs.target docker.service

[Service]
Type=simple
User=root
Group=root
Environment=HOME=/home/user
ExecStart=/home/user/backend.ai/agent/run-agent.sh
WorkingDirectory=/home/user/backend.ai/agent
KillMode=process
KillSignal=SIGTERM
PrivateTmp=false
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

`/home/user/backend.ai/agent/run-agent.sh`:

```sh
#! /bin/sh
if [ -z "$PYENV_ROOT" ]; then
  export PYENV_ROOT="$HOME/.pyenv"
  export PATH="$PYENV_ROOT/bin:$PATH"
fi
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

cd /home/user/backend.ai/agent
if [ "$#" -eq 0 ]; then
  sh /home/user/backend.ai/agent/scripts/update-metadata-iptables.sh
  exec python -m ai.backend.agent.server
else
  exec "$@"
fi
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


LICENSES
--------

[GNU Lesser General Public License](https://github.com/lablup/backend.ai-agent/blob/master/LICENSE)
[Dependencies](https://github.com/lablup/backend.ai-manager/blob/agent/DEPENDENCIES.md)
